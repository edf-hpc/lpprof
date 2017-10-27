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
import lpprofiler.metrics_manager as metm
import lpprofiler.perf_hwcounters_profiler as php
import lpprofiler.valgrind_memory_profiler as vmp
import sys, os, stat, re, datetime
#from jinja2 import Template


class LpProfiler :
    
    def __init__(self,launcher,pid,rank,binary,profiling_args):

        # Launcher name (ex: srun)
        self.launcher=launcher

        # Pid and rank of the processus to profile
        self.pid_to_profile=pid
        self.proc_rank=rank

        # If parallel rank is not given use pid as rank in output files
        if not self.proc_rank and pid:
            self.proc_rank=pid
        else:
            self.proc_rank="all"

        # Binary to profile
        self.binary=binary

        # Profiling options (TODO: should be customizable at launch )
        self.profiling_flavours=["asm_prof","hwcounters_prof"]

        self.global_metrics={}

        # Sample Manager ( Avg,Min,Max and count per rank)
        self.metrics_manager=metm.MetricsManager()

        if( 'output_dir' in profiling_args):
            self.traces_directory=profiling_args['output_dir']
        else:
            today=datetime.datetime.today()
            self.traces_directory="PERF_{}".format(today.isoformat())
            
        if not os.path.exists(self.traces_directory):
            os.mkdir(self.traces_directory)
        
        # Build profilers
        if (self.launcher)and('srun' in self.launcher):
            slurm_ntasks=int(os.environ["SLURM_NTASKS"])
            trace_samples="{}/perf.data_%t".format(self.traces_directory)
            trace_hwc="{}/perf.stats_%t".format(self.traces_directory)
            
            output_samples=[]
            output_hwc=[]
            for rank in range(0,slurm_ntasks-1):
                output_samples.append("{}/perf.data_{}".format(self.traces_directory,rank))
                output_hwc.append("{}/perf.stats_{}".format(self.traces_directory,rank))
            
        elif (self.launcher=='std'):
            trace_samples="{}/perf.data".format(self.traces_directory)
            trace_hwc="{}/perf.stats".format(self.traces_directory)
            output_samples=None
            output_hwc=None
        elif (self.pid_to_profile):
            trace_samples="{}/perf.data_{}".format(self.traces_directory,self.proc_rank)
            trace_hwc="{}/perf.stats_{}".format(self.traces_directory,self.proc_rank)
            output_samples=None
            output_hwc=None


        self.profilers=[
            php.PerfHWcountersProfiler(trace_hwc,self.metrics_manager,output_hwc,profiling_args),\
            psp.PerfSamplesProfiler(trace_samples,self.metrics_manager,output_samples,profiling_args)
        ]
        

    def _std_run_cmd(self):
        """ Run standard exe with perf profiling """

        run_cmd=''
        
        for prof in self.profilers :
            run_cmd+=prof.get_profile_cmd()
        
        run_cmd+=self.binary

        return run_cmd
                        
    def _slurm_run_cmd(self):
        """ Run slurm job with profiling """

        profile_cmd=""
        for prof in self.profilers :
            profile_cmd+=prof.get_profile_cmd()

        slurm_ntasks=os.environ["SLURM_NTASKS"]
        with open("./{}/lpprofiler.conf".format(self.traces_directory),"w") as f_conf:
            f_conf.write("0-{} bash ./{}/profile_cmd.sh %t".format(int(slurm_ntasks)-1,self.traces_directory))

        with open("./{}/profile_cmd.sh".format(self.traces_directory),"w") as f_cmd:
            f_cmd.write(profile_cmd.replace('%t','$1')+self.binary)


        st = os.stat("./{}/profile_cmd.sh".format(self.traces_directory))
        os.chmod("./{}/profile_cmd.sh".format(self.traces_directory),st.st_mode | stat.S_IEXEC)

        srun_argument="--cpu_bind=cores,verbose"
        srun_cmd='{} --multi-prog ./{}/lpprofiler.conf'.format(self.launcher,self.traces_directory)

        return srun_cmd

    def _pid_run_cmd(self):
        """ Profile a processus given its PID"""

        run_cmd=''
        
        for prof in self.profilers :
            run_cmd+=prof.get_profile_cmd(pid=self.pid_to_profile)

        # Use tail to stop profiling when profiled processus ends 
        run_cmd+=' tail --pid={} -f /dev/null'.format(self.pid_to_profile)

        return run_cmd


    def _lp_log(self,msg):
        if msg:
            with open("{}/lpprof_log_{}".format(self.traces_directory,self.proc_rank),"a") as logf:
                logf.write(msg)
        
    def run(self):
        """ Run job with profiling """

        prof_cmd=None
        # Execute profiling possibly with parallel launcher.
        if self.launcher and ('srun' in self.launcher):
            prof_cmd=self._slurm_run_cmd()
        elif (self.launcher=='std'):
            prof_cmd=self._std_run_cmd()
        elif (self.pid_to_profile):
            prof_cmd=self._pid_run_cmd()
        else:
            self._lp_log("Unsupported launcher: \n"+self.launcher)
            exit

        prof_process=Popen(prof_cmd,shell=True)
        # Wait for the command to finish
        prof_process.communicate()

        # Log the profiling command
        with open("{}/perf_cmd".format(self.traces_directory),"w") as pf:
            pf.write("Profiling command : {}".format(prof_cmd))

        # Calls to analyze
        for prof in self.profilers :
            prof.analyze()


    def report(self):
        """ Print profiling reports """

        print("Writing lpprof performance summary to : {}/lpprof_log_{}".format(self.traces_directory,self.proc_rank))

        self._lp_log("\n")

        # Print hardware counters
        for metric_type in ['hwc','vectorization','asm','sym']:

            if not self.metrics_manager.get_metric_names_sorted(metric_type):
                continue
            
            title=metric_type+" metrics:"
            self._lp_log(title+"\n")
            self._lp_log("".ljust(len(title),"-"))
            self._lp_log("\n\n")
            self._lp_log("  metric name".ljust(40))
            self._lp_log("min".ljust(40))
            self._lp_log("max".ljust(40))
            self._lp_log("avg".ljust(40))
            self._lp_log("\n")
            self._lp_log("  ".ljust(160,"-"))
            self._lp_log("\n")
            metric_unit=''
            if metric_type in ['asm','sym']:
                metric_unit='%'
            
            for metric_name in self.metrics_manager.get_metric_names_sorted(metric_type):

                
                self._lp_log("  {} ".format(metric_name).ljust(40))
                self._lp_log("{:.5g}{}".format(
                    self.metrics_manager.get_metric_min(metric_type,metric_name)[0],metric_unit).ljust(10))
                self._lp_log("    (rank: {})".format(
                    self.metrics_manager.get_metric_min(metric_type,metric_name)[1]).ljust(30))
                self._lp_log("{:.5g}{}".format(
                    self.metrics_manager.get_metric_max(metric_type,metric_name)[0],metric_unit).ljust(10))
                self._lp_log("    (rank: {})".format(
                    self.metrics_manager.get_metric_max(metric_type,metric_name)[1]).ljust(30))
                self._lp_log("{:.5g}{}".format(
                    self.metrics_manager.get_metric_avg(metric_type,metric_name),metric_unit).ljust(40))
                self._lp_log("\n")

            self._lp_log("\n\n")
        self._lp_log("\n")
                    


            
        
