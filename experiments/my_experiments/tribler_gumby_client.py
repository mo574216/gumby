#!/usr/bin/env python
# dispersyclient.py ---
#
# Filename: dispersyclient.py
# Description:
# Author: Elric Milon
# Maintainer:Seyedakbar Mostafavi
# Created: Wed Sep 18 17:29:33 2013 (+0200)
# Changed: May 14 2014
# Commentary:
# I plan to customize this file to run tribler with my config file
#
#
#

# Change Log:
#
#
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.
#
#

# Code:

from os import environ, path, chdir, makedirs, symlink, getpid
from sys import stdout, exit, stderr
from collections import defaultdict, Iterable
import json
from time import time
from random import random

from gumby.sync import ExperimentClient, ExperimentClientFactory
from gumby.scenario import ScenarioRunner
from gumby.log import setupLogging

from twisted.python.log import msg, err

# The reactor needs to be imported after the dispersy client, as it is installing an EPOLL based one.
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
import base64
from traceback import print_exc

class TriblerExperimentScriptClient(ExperimentClient):
    scenario_file = None

    def __init__(self, vars):
        ExperimentClient.__init__(self, vars)

    def onVarsSend(self):
        scenario_file_path = path.join(environ['EXPERIMENT_DIR'], self.scenario_file)
        self.scenario_runner = ScenarioRunner(scenario_file_path)

        t1 = time()
        self.scenario_runner._read_scenario(scenario_file_path)
        msg('Took %.2f to read scenario file' % (time() - t1))

    def onIdReceived(self):
        self.scenario_runner.set_peernumber(int(self.my_id))
        self.registerCallbacks()

        t1 = time()
        self.scenario_runner.parse_file()
        msg('Took %.2f to parse scenario file' % (time() - t1))

    def startExperiment(self):
        msg("Starting tribler scenario experiment")

        my_dir = path.join(environ['OUTPUT_DIR'], self.my_id)
        makedirs(my_dir)
        chdir(my_dir)
        self._stats_file = open("statistics.log", 'w')

        # TODO(emilon): Fix me or kill me
        try:
            symlink(path.join(environ['PROJECT_DIR'], 'tribler', 'bootstraptribler.txt'), 'bootstraptribler.txt')
        except OSError:
            pass

        self.scenario_runner.run()

    def registerCallbacks(self):
        pass

    def echo(self, *argv):
        msg("%s ECHO" % self.my_id, ' '.join(argv))

    #
    # Aux. functions
    #


   def str2bool(self, v):
        return v.lower() in ("yes", "true", "t", "1")

    def str2tuple(self, v):
        if len(v) > 1 and v[1] == "t":
            return (int(v[0]), int(v[2:]))
        if len(v) > 1 and v[1] == ".":
            return float(v)
        return int(v)

    def _do_log(self):
        from Tribler.dispersy.candidate import CANDIDATE_STUMBLE_LIFETIME, CANDIDATE_WALK_LIFETIME, CANDIDATE_INTRO_LIFETIME
        total_stumbled_candidates = defaultdict(lambda:defaultdict(set))

        prev_statistics = {}
        prev_total_received = {}
        prev_total_dropped = {}
        prev_total_delayed = {}
        prev_total_outgoing = {}
        prev_total_fail = {}
        prev_endpoint_recv = {}
        prev_endpoint_send = {}
        prev_created_messages = {}
        prev_bootstrap_candidates = {}

        while True:
            self._dispersy.statistics.update()

            communities_dict = {}
            for c in self._dispersy.statistics.communities:

                if c._community.dispersy_enable_candidate_walker:
                    # determine current size of candidates categories
                    nr_walked = nr_intro = nr_stumbled = 0

                    # we add all candidates which have a last_stumble > now - CANDIDATE_STUMBLE_LIFETIME
                    now = time()
                    for candidate in c._community.candidates.itervalues():
                        if candidate.last_stumble > now - CANDIDATE_STUMBLE_LIFETIME:
                            nr_stumbled += 1

                            mid = list(candidate.get_members())[0].mid
                            total_stumbled_candidates[c.hex_cid][candidate.last_stumble].add(mid)

                        if candidate.last_walk > now - CANDIDATE_WALK_LIFETIME:
                            nr_walked += 1

                        if candidate.last_intro > now - CANDIDATE_INTRO_LIFETIME:
                            nr_intro += 1
                else:
                    nr_walked = nr_intro = nr_stumbled = "?"

                total_nr_stumbled_candidates = sum(len(members) for members in total_stumbled_candidates[c.hex_cid].values())

                communities_dict[c.hex_cid] = {'classification': c.classification,
                                         'global_time': c.global_time,
                                         'sync_bloom_new': c.sync_bloom_new,
                                         'sync_bloom_reuse': c.sync_bloom_reuse,
                                         'sync_bloom_send': c.sync_bloom_send,
                                         'sync_bloom_skip': c.sync_bloom_skip,
                                         'nr_candidates': len(c.candidates) if c.candidates else 0,
                                         'nr_walked': nr_walked,
                                         'nr_stumbled': nr_stumbled,
                                         'nr_intro' : nr_intro,
                                         'total_stumbled_candidates': total_nr_stumbled_candidates}

            # check for missing communities, reset candidates to 0
            cur_cids = communities_dict.keys()
            for cid, c in prev_statistics.get('communities', {}).iteritems():
                if cid not in cur_cids:
                    _c = c.copy()
                    _c['nr_candidates'] = "?"
                    _c['nr_walked'] = "?"
                    _c['nr_stumbled'] = "?"
                    _c['nr_intro'] = "?"
                    communities_dict[cid] = _c

            statistics_dict = {'conn_type': self._dispersy.statistics.connection_type,
                               'received_count': self._dispersy.statistics.received_count,
                               'success_count': self._dispersy.statistics.success_count,
                               'drop_count': self._dispersy.statistics.drop_count,
                               'delay_count': self._dispersy.statistics.delay_count,
                               'delay_success': self._dispersy.statistics.delay_success,
                               'delay_timeout': self._dispersy.statistics.delay_timeout,
                               'delay_send': self._dispersy.statistics.delay_send,
                               'created_count': self._dispersy.statistics.created_count,
                               'total_up': self._dispersy.statistics.total_up,
                               'total_down': self._dispersy.statistics.total_down,
                               'total_send': self._dispersy.statistics.total_send,
                               'cur_sendqueue': self._dispersy.statistics.cur_sendqueue,
                               'total_candidates_discovered': self._dispersy.statistics.total_candidates_discovered,
                               'walk_attempt': self._dispersy.statistics.walk_attempt,
                               'walk_success': self._dispersy.statistics.walk_success,
                               'walk_bootstrap_attempt': self._dispersy.statistics.walk_bootstrap_attempt,
                               'walk_bootstrap_success': self._dispersy.statistics.walk_bootstrap_success,
                               'walk_invalid_response_identifier': self._dispersy.statistics.walk_invalid_response_identifier,
                               'walk_advice_outgoing_request': self._dispersy.statistics.walk_advice_outgoing_request,
                               'walk_advice_incoming_response': self._dispersy.statistics.walk_advice_incoming_response,
                               'walk_advice_incoming_response_new': self._dispersy.statistics.walk_advice_incoming_response_new,
                               'walk_advice_incoming_request': self._dispersy.statistics.walk_advice_incoming_request,
                               'walk_advice_outgoing_response': self._dispersy.statistics.walk_advice_outgoing_response,
                               'is_online': self.is_online(),
                               'communities': communities_dict}

            prev_statistics = self.print_on_change("statistics", prev_statistics, statistics_dict)
            prev_total_dropped = self.print_on_change("statistics-dropped-messages", prev_total_dropped, self._dispersy.statistics.drop)
            prev_total_delayed = self.print_on_change("statistics-delayed-messages", prev_total_delayed, self._dispersy.statistics.delay)
            prev_total_received = self.print_on_change("statistics-successful-messages", prev_total_received, self._dispersy.statistics.success)
            prev_total_outgoing = self.print_on_change("statistics-outgoing-messages", prev_total_outgoing, self._dispersy.statistics.outgoing)
            prev_created_messages = self.print_on_change("statistics-created-messages", prev_created_messages, self._dispersy.statistics.created)
            prev_total_fail = self.print_on_change("statistics-walk-fail", prev_total_fail, self._dispersy.statistics.walk_fail)
            prev_endpoint_recv = self.print_on_change("statistics-endpoint-recv", prev_endpoint_recv, self._dispersy.statistics.endpoint_recv)
            prev_endpoint_send = self.print_on_change("statistics-endpoint-send", prev_endpoint_send, self._dispersy.statistics.endpoint_send)
            prev_bootstrap_candidates = self.print_on_change("statistics-bootstrap-candidates", prev_bootstrap_candidates, self._dispersy.statistics.bootstrap_candidates)

            yield 5.0


def main(client_class):
    setupLogging()
    factory = ExperimentClientFactory({}, client_class)
    msg("Connecting to: %s:%s" % (environ['SYNC_HOST'], int(environ['SYNC_PORT'])))
    # Wait for a random amount of time before connecting to try to not overload the server when we have a lot of connections
    reactor.callLater(random() * 10,
                      lambda: reactor.connectTCP(environ['SYNC_HOST'], int(environ['SYNC_PORT']), factory))
    reactor.exitCode = 0
    reactor.run()
    exit(reactor.exitCode)

#
# dispersyclient.py ends here

if __name__ == '__main__':
    import sys
    dc = TriblerExperimentScriptClient({})
    dc._stats_file = sys.stderr
