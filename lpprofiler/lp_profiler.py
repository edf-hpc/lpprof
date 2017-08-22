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
import lpprofiler.perf_samples_profiler as psp
import lpprofiler.perf_hwcounters_profiler as php
import sys, os, re


class LpProfiler :
    
    def __init__(self,launcher,launcher_args,binary):

        # Launcher name (ex: srun)
        self.launcher=launcher

        # Launcher arguments
        self.launcher_args=launcher_args

        # Binary to profile
        self.binary=binary

        # Profiling options (TODO: should be customizable at launch )
        self.profiling_flavours=["asm_prof","hwcounters_prof"]

        # List of profilers
        if (self.launcher=='srun'):
            os.mkdir("PERF")
            self.profilers=[php.PerfHWcountersProfiler("./PERF/perf.stats_%t",["./PERF/perf.stats_0"]),\
                            psp.PerfSamplesProfiler("./PERF/perf.data_%t",["./PERF/perf.data_0"])]
        elif (self.launcher=='std'):
            os.mkdir("PERF")
            self.profilers=[php.PerfHWcountersProfiler("./PERF/perf.stats"),\
                            psp.PerfSamplesProfiler("./PERF/perf.data")]
    
    def _std_run(self,frequency):
        """ Run standard exe with perf profiling """

        for prof in self.profilers :
            run_cmd+=prof.get_profile_cmd()
        
        run_cmd+=binary
        srun_process=Popen(run_cmd,shell=True)
        # Wait for the command to finish
        run_process.communicate()

                        
    def _slurm_run(self,frequency):
        """ Run slurm job with profiling """
        prepare_cmd='ntasks=$(($SLURM_NTASKS - 1)); '
        prepare_cmd+='echo "0-$ntasks '

        for prof in self.profilers :
            prepare_cmd+=prof.get_profile_cmd()
   
        prepare_cmd+=' {} "> lpprofiler.conf'.format(self.binary)

        prepare_process=Popen(prepare_cmd,shell=True, stdout=PIPE,stderr=PIPE)
        stdout,stderr=prepare_process.communicate()

        if stderr:
            print("Error while writing slurm multiprog configuration file for profiling: "\
                  +stderr.decode('utf-8'))
            exit

        srun_argument="--cpu_bind=cores,verbose"
        srun_cmd="srun {} --multi-prog lpprofiler.conf".format(self.launcher_args)
        srun_process=Popen(srun_cmd,shell=True)
        # Wait for the command to finish
        srun_process.communicate()

    
    def run(self,frequency="99"):
        """ Run job with profiling """

        # Execute profiling possibly with parallel launcher.
        if (self.launcher=='srun'):
            self._slurm_run(frequency)
        elif (self.launcher=='std'):
            self._std_run(frequency)
        else :
            print("Unsupported launcher: "+self.launcher)
            exit

        # Calls to analyze
        for prof in self.profilers :
            prof.analyze()
            
                
    def report(self):
        """ Print profiling reports """
        for prof in self.profilers :
            prof.report()
                    

        
