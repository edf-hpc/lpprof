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

        self._launcher=launcher
        self._launcher_args=launcher_args
        self._binary=binary        
        self._perf_samples_analyzer=None
        self._samples_file=None

    def _std_run(self,frequency):
        """ Run standard exe with perf profiling"""
        run_cmd='perf record -g -F {} -o perf.data {}'.format(frequency,self._binary)
        srun_process=Popen(run_cmd,shell=True,stdout=PIPE,stderr=PIPE)
        print("Start profiling ...")
        stdout,stderr=run_process.communicate()
        self._perf_samples_analyzer=psa.PerfSamplesAnalyzer("./PERF/perf.data")
                        
    def _slurm_run(self,frequency):
        """ Run slurm job with profiling"""
        prepare_cmd='ntasks=$(($SLURM_NTASKS - 1)); '
        prepare_cmd+='mkdir -p PERF; '
        prepare_cmd+='echo "0-$ntasks perf record -g -F {} -o '.format(frequency)+\
            './PERF/perf.data_%t {}" > profile.conf'.format(self._binary)
        
        prepare_process=Popen(prepare_cmd,shell=True, stdout=PIPE,stderr=PIPE)
        stdout,stderr=prepare_process.communicate()

        if stderr:
            print("Error while slurm multiprog configuration file for profiling: "\
                  +stderr.decode('utf-8'))
            exit

        srun_argument="--cpu_bind=cores,verbose"
        srun_cmd="srun {} --multi-prog profile.conf".format(self._launcher_args)
        srun_process=Popen(srun_cmd,shell=True,stdout=PIPE,stderr=PIPE)

        print("Start profiling ...")
        stdout,stderr=srun_process.communicate()
        self._perf_samples_analyzer=psa.PerfSamplesAnalyzer("./PERF/perf.data_0")

        
    def run(self,frequency="99"):
        """ Run job with profiling"""
        if (self._launcher=='srun'):
            self._slurm_run(frequency)
        else :
            print("Unsupported launcher: "+self._launcher)
            exit

                
    def analyze(self):
        """ Analyze samples collected by profiling"""
        if (self._perf_samples_analyzer):
            self._perf_samples_analyzer.analyze_perf_samples()
            self._perf_samples_analyzer.report_assembly_usage()
        else:
            print("Error: no sample found")

        
