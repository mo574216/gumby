#!/usr/bin/env python
# tribler_run.py ---
#
# Filename: tribler_run.py
# Description:
# Author: Seyedakbar Mostafavi
# Maintainer:
# Created: Thu May 15, 2014

# Commentary:
# Run Tribler as server
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

import sys
import os

os.chdir(os.path.abspath('./tribler'))
sys.path.append('.')

from Tribler.Test.test_as_server import TestGuiAsServer


class TestServerGeneral(TestGuiAsServer):
    """Run Tribler for 100 seconds """

    def __init__(self):
        """ empty constructor """
        pass

    def call_tribler(self):
        """call Tribler """
        if "TRIBLER_EXECUTION_TIME" in os.environ:
            run_time = "TRIBLER_EXECUTION_TIME"
        else:
            run_time = 60*4
        self.Call(run_time, self.quit())

    def test_tribler(self):
        """call function to run tribler """
        self.call_tribler()

if __name__ == "__main__":
    # instantiate and call functions
    t1 = TestServerGeneral()
    t1.test_tribler()

# tribler_run.py ends here
