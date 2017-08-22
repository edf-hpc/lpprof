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
        
        if output_files:
            self.output_files=output_files
        else:
            self.output_files=[self.trace_file]

        self.hwcounters_count_dic={}
    
    def get_profile_cmd(self):
        """ Hardware counters profiling command """
        # Add a delay of 1 second to avoid counting 'perf record' launching hw counters stats.
        return "perf stat -x / -e instructions,cycles -D 1000 -o {} ".format(self.trace_file)

    def analyze(self):
        """ Sum hardware counters over evry output file and compute the mean. """
        for stats_file in self.output_files:
            with open(stats_file,'r') as sf:
                for line in sf:
                    splitted_line=line.rstrip().split("//")
                    if len(splitted_line)==2:
                        if splitted_line[1] in self.hwcounters_count_dic:
                            self.hwcounters_count_dic[splitted_line[1]]+=int(splitted_line[0])
                        else:
                            self.hwcounters_count_dic[splitted_line[1]]=int(splitted_line[0])

        for hwcounter in self.hwcounters_count_dic:
            self.hwcounters_count_dic[hwcounter]/=len(self.output_files)
            
                        

    def report(self):
        """ Standard global reporting method """
        self.report_inspercycle()

    def report_inspercycle(self):

        if ("instructions" in self.hwcounters_count_dic) and ("cycles" in self.hwcounters_count_dic) :
            nb_ins=self.hwcounters_count_dic["instructions"]
            nb_cycles=self.hwcounters_count_dic["cycles"]
            
        print("Instructions per cycle : "+str(nb_ins/nb_cycles))
            

    def report_tlbmiss(self):
        pass
        
            
