# -*- coding: utf-8 -*-
##############################################################################
#  This file is part of the LPprofiler profiling tool.                       #
#        Copyright (C) 2017  EDF SA                                          #
#                                                                            #
#  LPprofiler is free software: you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by      #
#  the Free Software Foundation, either version 3 of the License, or         #
#  (at your option) any later version.                                       #
#                                                                            #
#  LPprofiler is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#  GNU General Public License for more details.                              #
#                                                                            #
#  You should have received a copy of the GNU General Public License         #
#  along with LPprofiler.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                            #
############################################################################## 

from subprocess import Popen,PIPE
import sys
import re
import os
        
class PerfHWcountersProfiler :

    def __init__(self,trace_file,output_files=None):
        self.trace_file=trace_file
        
        if not(output_files):
            output_files=[self.trace_file]
            
    
    def get_profile_cmd(self):
        """ Hardware counters profiling command """
        # Add a delay of 1 second to avoid counting 'perf record' launching hw counters stats.
        return "perf stat -x / -e instructions,cycles -D 1000 -o {} ".format(self.trace_file)

    def analyze(self):
        pass

    def report(self):
        """ Standard global reporting method """
        self.report_inscount()

    def report_inscount(self):
        pass

    def report_tlbmiss(self):
        pass
        
            
