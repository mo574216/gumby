#!/usr/bin/env python
# tribler_gumby_client.py ---
#
# Filename: tribler_gumby_client.py
# Description:
# Author: Elric Milon
# Maintainer:Seyedakbar Mostafavi
# Created: Wed Sep 18 17:29:33 2013 (+0200)
# Changed: May 14 2014
# Commentary:
# I plan to customize this file to run tribler with my scnario file
#
#
#

# Change Log:
# Delete dispersy stuff
# Register my functions
# Define my functions
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
	self.scenario_runner.register(self.start_tribler)
	self.scenario_runner.register(self.online)
	self.scenario_runner.register(self.stop_tribler)
	self.scenario_runner.register(self.stop)

	
        self.registerCallbacks()

        t1 = time()
        self.scenario_runner.parse_file()
        msg('Took %.2f to parse scenario file' % (time() - t1))

    def startExperiment(self):
        msg("Starting tribler scenario experiment")


        # TODO(emilon): Fix me or kill me
        try:
            symlink(path.join(environ['PROJECT_DIR'], 'tribler', 'bootstraptribler.txt'), 'bootstraptribler.txt')
        except OSError:
            pass

        self.scenario_runner.run()

    def registerCallbacks(self):
        pass
    def start_tribler():
	msg("Starting tribler")
	from Tribler.Main.tribler.py import run
	
    def online(self):
	msg("online")

    def stop_tribler(self):
	msg("offline")

    def stop(self):
	msg("stop experiment")


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
