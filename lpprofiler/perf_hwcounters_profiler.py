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
import lpprofiler.profiler as prof
import sys, re, os
        
class PerfHWcountersProfiler(prof.Profiler) :

    def __init__(self,trace_file,output_files=None,profiling_args=None):
        """ Constructor """
        
        prof.Profiler.__init__(self, trace_file,output_files,profiling_args)

        # Dictionnary containing count for each monitored hardware counter
        self.hwc_count_dic={}


    @property
    def global_metrics(self):
        """ Return a dictionnary with metrics that could be used outside this pofiler """
        return self.hwc_count_dic
        
    
    def get_profile_cmd(self):
        """ Hardware counters profiling command """
        # Add a delay of 1 second to avoid counting 'perf record' launching hw counters stats.
        counters=[]
        counters.append("instructions")
        counters.append("cycles")
        counters.append("cpu/event=0x08,umask=0x10,name=dTLBmiss_cycles/")
        counters.append("cpu/event=0x85,umask=0x10,name=iTLBmiss_cycles/")
        counters.append("cpu-clock")
        
        return "perf stat -x / -e {} -D 1000 -o {} ".format(','.join(counters),self.trace_file)


    
    def analyze(self):
        """ Sum hardware counters over evry output file and compute the mean. """
        for stats_file in self.output_files:
            with open(stats_file,'r') as sf:
                for line in sf:
                    splitted_line=line.rstrip().split("//")
                    if len(splitted_line)==2:
                        # Convert , to . to be sure floats are well formatted
                        local_count=float(splitted_line[0].replace(',', '.'))
                        if splitted_line[1] in self.hwc_count_dic:
                            self.hwc_count_dic[splitted_line[1]]+=local_count
                        else:
                            self.hwc_count_dic[splitted_line[1]]=local_count

        for hwcounter in self.hwc_count_dic:
            self.hwc_count_dic[hwcounter]/=len(self.output_files)
            
                        

    def report(self):
        """ Standard global reporting method """
        pass

        
            
