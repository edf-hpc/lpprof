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
import lpprofiler.perf_samples_analyzer as psa
import sys
import re


class LpProfiler :
    
    def __init__(self,launcher,launcher_args,binary):

        # Launcher name (ex: srun)
        self.launcher=launcher

        # Launcher arguments
        self.launcher_args=launcher_args

        # Binary to profile
        self.binary=binary

        # Sample analyzer instance
        self.perf_samples_analyzer=None

        # Profiling options (TODO: should be customizable at launch )
        self.profiling_flavours=["asm_prof","hwcounters_prof"]


    def _get_asm_profile_cmd(self,frequency,output_file):
        """ Assembly instructions profiling command """
        return "perf record -g -F {} -o {} ".format(frequency,output_file)

    def _get_hwcounters_profile_cmd(self,output_file):
        """ Hardware counters profiling command """
        return "perf stat -e instructions,cycles -D 1000 -o {} ".format(output_file)

    
    def _std_run(self,frequency):
        """ Run standard exe with perf profiling """

        run_cmd='mkdir -p PERF; '
        if ("hwcounters_prof" in self.profiling_flavours):
            run_cmd+=self._get_hwcounters_profile_cmd("./PERF/perf.data")
        if ("asm_prof" in self.profiling_flavours):
            run_cmd+=self._get_asm_profile_cmd(frequency,"./PERF/perf.stats")
        
        srun_process=Popen(run_cmd+self.binary,shell=True,stdout=PIPE,stderr=PIPE)
        print("Start profiling ...")
        stdout,stderr=run_process.communicate()

        # Build perf sample analyzer
        self.perf_samples_analyzer=psa.PerfSamplesAnalyzer("./PERF/perf.data")
        
                        
    def _slurm_run(self,frequency):
        """ Run slurm job with profiling """
        prepare_cmd='ntasks=$(($SLURM_NTASKS - 1)); '
        prepare_cmd+='mkdir -p PERF; '
        prepare_cmd+='echo "0-$ntasks '
        
        if ("hwcounters_prof" in self.profiling_flavours):
            prepare_cmd+=self._get_hwcounters_profile_cmd("./PERF/perf.stats_%t")
            
        if ("asm_prof" in self.profiling_flavours):
            prepare_cmd+=self._get_asm_profile_cmd(frequency,"./PERF/perf.data_%t")
            
        prepare_cmd+=' {} "> lpprofiler.conf'.format(self.binary)


        print("prepare_cmd: "+prepare_cmd)
        
        prepare_process=Popen(prepare_cmd,shell=True, stdout=PIPE,stderr=PIPE)
        stdout,stderr=prepare_process.communicate()

        if stderr:
            print("Error while writing slurm multiprog configuration file for profiling: "\
                  +stderr.decode('utf-8'))
            exit

        srun_argument="--cpu_bind=cores,verbose"
        srun_cmd="srun {} --multi-prog lpprofiler.conf".format(self.launcher_args)
        srun_process=Popen(srun_cmd,shell=True,stdout=PIPE,stderr=PIPE)

        print("Start profiling ...")
        stdout,stderr=srun_process.communicate()

        # Analyze only the result of rank 0
        self.perf_samples_analyzer=psa.PerfSamplesAnalyzer("./PERF/perf.data_0")

        
    def run(self,frequency="99"):
        """ Run job with profiling """
        if (self.launcher=='srun'):
            self._slurm_run(frequency)
        elif (self.launcher=='std'):
            self._std_run(frequency)
        else :
            print("Unsupported launcher: "+self.launcher)
            exit

                
    def report(self):
        """ Print profiling report """
        if (self.perf_samples_analyzer):
            self.perf_samples_analyzer.report_assembly_usage()
        else:
            print("Error: no sample found")

        
