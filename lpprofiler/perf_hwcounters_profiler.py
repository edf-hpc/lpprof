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
import lpprofiler.metrics_manager as metm
import sys, re, os


class PerfHWcountersProfiler(prof.Profiler) :

    def __init__(self,metrics_manager,trace_files,output_files=None,profiling_args=None):
        """ Constructor """
        
        prof.Profiler.__init__(self,metrics_manager,trace_files,output_files,profiling_args)

    
    def get_profile_cmd(self,pid=None,rank=None):
        """ Hardware counters profiling command """
        # Add a delay of 100 milliseconds to avoid counting 'perf record' launching hw counters stats.
        counters=[]
        counters.append("instructions")
        counters.append("cycles")
        counters.append("cpu-clock")
        counters.append("task-clock")
        counters.append("cpu/event=0x08,umask=0x10,name=dTLBmiss_cycles/")
        counters.append("cpu/event=0x85,umask=0x10,name=iTLBmiss_cycles/")

        if pid and rank:
            return "perf stat --pid={} -x / -e {} -D 100 -o {} ".format(pid,','.join(counters),self.trace_files[rank])
        else:
            return "perf stat -x / -e {} -D 100 -o {} ".format(','.join(counters),self.trace_files[0])


    
    def analyze(self,ranks=None):
        """ Sum hardware counters over evry output file and compute the mean. """
        irank=0
        metric_type="hwc"        
        for stats_file in self.output_files:

            if(ranks):
                rank=ranks[irank]
            else:
                rank=irank
            
            with open(stats_file,'r') as sf:
                for line in sf:
                    splitted_line=line.rstrip().split("//")
                    if len(splitted_line)==2:
                        # Convert , to . to be sure floats are well formatted
                        try :
                            local_count=float(splitted_line[0].replace(',', '.'))
                        except ValueError:
                            print("Cannot convert hardware counter {} to float.".format(splitted_line[1]))
                            print("Program may be too short (no value) or counter is not valid.")
                            exit

                        metric_name=splitted_line[1]
                        self.metrics_manager.add_metric(rank,metric_type,metric_name,local_count)

            # Derivated metrics
            ins=float(self.metrics_manager.get_metric_count(metric_type,'instructions',rank))
            cycles=float(self.metrics_manager.get_metric_count(metric_type,'cycles',rank))
            if ins>0 and cycles>0:
                self.metrics_manager.add_metric(
                    rank,metric_type,'ins-per-cycle',ins/cycles)
            else :
                print("ins"+str(ins)+"cycles"+str(cycles))

            itlb_miss=float(self.metrics_manager.get_metric_count(metric_type,'dTLBmiss_cycles',rank))
            dtlb_miss=float(self.metrics_manager.get_metric_count(metric_type,'iTLBmiss_cycles',rank))

            if ins>0 and itlb_miss>0 and dtlb_miss>0:
                self.metrics_manager.add_metric(
                    rank,metric_type,'cycles spent due to TLBmiss (%)',
                    (itlb_miss+dtlb_miss)/cycles)
                
            irank+=1
        self.metrics_manager.remove_metric(metric_type,'instructions')
        self.metrics_manager.remove_metric(metric_type,'dTLBmiss_cycles')
        self.metrics_manager.remove_metric(metric_type,'iTLBmiss_cycles')


        
            
