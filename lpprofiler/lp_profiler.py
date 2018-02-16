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
    
    def __init__(self,launcher,pids,ranks,binary,profiling_args):

        # Launcher name (ex: srun)
        self.launcher=launcher

        # Pid and rank of the processus to profile
        self.pids_to_profile=pids
        self.ranks_to_profile=ranks
        

        # Binary to profile
        self.binary=binary

        # Profiling options (TODO: should be customizable at launch )
        self.profiling_flavours=["asm_prof","hwcounters_prof"]

        self.global_metrics={}

        # Sample Manager ( Avg,Min,Max and count per rank)
        self.metrics_manager=metm.MetricsManager()

        if( 'output_dir' in profiling_args):
            self.traces_directory=profiling_args['output_dir']
        elif(os.environ.get('SLURM_JOB_ID')):
            self.traces_directory="perf_{}".format(os.environ.get('SLURM_JOB_ID'))
        else:
            today=datetime.datetime.today()
            self.traces_directory="perf_{}".format(today.isoformat())
            
        if not os.path.exists(self.traces_directory):
            os.mkdir(self.traces_directory)
        
        # Build profilers
        trace_samples=[]
        trace_hwc=[]
        output_samples=[]
        output_hwc=[]
        if (self.launcher)and('srun' in self.launcher):
            slurm_ntasks=int(os.environ["SLURM_NTASKS"])
            trace_samples=["{}/perf.data_%t".format(self.traces_directory)]
            trace_hwc=["{}/perf.stats_%t".format(self.traces_directory)]
            for rank in range(0,slurm_ntasks):
                if (not self.ranks_to_profile) or (rank in self.ranks_to_profile):
                    output_samples.append("{}/perf.data_{}".format(self.traces_directory,rank))
                    output_hwc.append("{}/perf.stats_{}".format(self.traces_directory,rank))
        elif (self.launcher=='std'):
            trace_samples=["{}/perf.data".format(self.traces_directory)]
            trace_hwc=["{}/perf.stats".format(self.traces_directory)]
        elif (self.pids_to_profile):
            # Ranks are attributed according to the position of the pid in the input pid list
            for rank in range(0,len(self.pids_to_profile)):
                if (not self.ranks_to_profile) or (rank in self.ranks_to_profile):
                    trace_samples.append("{}/perf.data_{}".format(self.traces_directory,rank))
                    trace_hwc.append("{}/perf.stats_{}".format(self.traces_directory,rank))

        self.profilers=[
            php.PerfHWcountersProfiler(self.metrics_manager,trace_hwc,output_hwc,profiling_args),\
            psp.PerfSamplesProfiler(self.metrics_manager,trace_samples,output_samples,profiling_args)
        ]
        

    def _std_run_cmd(self):
        """ Run standard exe with perf profiling """
        run_cmd=''
        
        for prof in self.profilers :
            run_cmd+=prof.get_profile_cmd()
        
        run_cmd+=self.binary

        return [run_cmd]


    def _append_slurm_conf(self,first_rank,last_rank,profile=False):

        
        with open("./{}/lpprofiler.conf".format(self.traces_directory),"a") as f_conf:
            if profile:
                if (first_rank!=last_rank):
                    f_conf.write("{}-{} bash ./{}/profile_cmd.sh %t\n".format(first_rank,last_rank,self.traces_directory))
                else:
                    f_conf.write("{} bash ./{}/profile_cmd.sh {}\n".format(first_rank,self.traces_directory,first_rank))
                
            else:
                f_conf.write("{}-{} {}\n".format(first_rank,last_rank,self.binary))
                    
    
    def _print_slurm_conf(self,nbranks):
        """ Print slurm multiprog conf file with """
        # first ranks of profile and no profile intervals
        rank_b_profile=-1
        rank_b_noprofile=-1
        last_rank=nbranks-1
        for rank in range(0,nbranks):
            if not self.ranks_to_profile or rank in self.ranks_to_profile:
                if rank_b_profile==-1:
                    rank_b_profile=rank
                    if rank_b_noprofile >= 0:
                        self._append_slurm_conf(rank_b_noprofile,rank-1,False)
                        rank_b_noprofile=-1
                if rank==last_rank:
                    self._append_slurm_conf(rank_b_profile,rank,True)
            else:
                if rank_b_noprofile==-1:
                    rank_b_noprofile=rank
                    if rank_b_profile >= 0:
                        self._append_slurm_conf(rank_b_profile,rank-1,True)
                        rank_b_profile=-1
                if rank==last_rank:
                    self._append_slurm_conf(rank_b_noprofile,rank,False)
        
        
    def _slurm_run_cmd(self):
        """ Run slurm job with profiling """

        profile_cmd=""
        for prof in self.profilers :
            profile_cmd+=prof.get_profile_cmd()

        slurm_ntasks=int(os.environ["SLURM_NTASKS"])

        
        self.ranks_to_profile

        self._print_slurm_conf(slurm_ntasks)
        
        with open("./{}/profile_cmd.sh".format(self.traces_directory),"w") as f_cmd:
            f_cmd.write(profile_cmd.replace('%t','$1')+self.binary)


        st = os.stat("./{}/profile_cmd.sh".format(self.traces_directory))
        os.chmod("./{}/profile_cmd.sh".format(self.traces_directory),st.st_mode | stat.S_IEXEC)

        srun_argument="--cpu_bind=cores,verbose"
        srun_cmd='{} --multi-prog ./{}/lpprofiler.conf'.format(self.launcher,self.traces_directory)

        return [srun_cmd]

    def _pid_run_cmd(self):
        """ Profile a processus given its PID"""

        run_cmds=[]

        rank=0
        irank=0
        for pid in self.pids_to_profile:
            run_cmd=''
            if (not self.ranks_to_profile) or (rank in self.ranks_to_profile):

                pid_num=int(pid.split(':')[-1])
                pid_host=pid.split(':')[0]
                
                for prof in self.profilers :
                    run_cmd+=prof.get_profile_cmd(pid_num,irank)
                # Wait for tasks to start before starting perf
                run_cmd='while [[ $(ps -p {} --no-headers -o comm) == slurmstepd ]]; do sleep 0.1; done; '.format(pid_num)+run_cmd
                # Wait for job to finish
                run_cmd+='bash -c "while [ ! -e {}/job_done ] && [ -e /proc/{} ]; do sleep 2; done"'.format(os.path.abspath("."),pid_num)

                # If an hostname is given prefix command by a ssh call
                if (len(pid.split(':'))>1):
                    run_cmd="ssh {} '{}'".format(pid_host,run_cmd)
                    
                irank+=1

                
            run_cmds.append(run_cmd)
            rank+=1
                
        return run_cmds


    def _lp_log(self,msg):
        if msg:
            with open("{}/LPprof_perf_report".format(self.traces_directory),"a") as logf:
                logf.write(msg)
        
    def run(self):
        """ Run job with profiling """

        prof_cmds=[]
        # Execute profiling possibly with parallel launcher.
        if self.launcher and ('srun' in self.launcher):
            prof_cmds=self._slurm_run_cmd()
        elif (self.launcher=='std'):
            prof_cmds=self._std_run_cmd()
        elif (self.pids_to_profile):
            prof_cmds=self._pid_run_cmd()
        else:
            self._lp_log("Unsupported launcher: \n"+self.launcher)
            exit

        # Launch profiling commands 
        prof_processes=[]
        for p_cmd in prof_cmds:
            prof_processes.append(Popen(p_cmd,shell=True))
        
        # Log the profiling command
        with open("{}/perf_cmds".format(self.traces_directory),"a") as pf:
            pf.write("Profiling commands :\n")
            for p_cmd in prof_cmds:
                pf.write(p_cmd+'\n')
                
        # Wait for profiling commands to finish
        for p_process in prof_processes:
            p_process.communicate()


        # Calls to analyze
        for prof in self.profilers :
            prof.analyze(self.ranks_to_profile)


    def report(self):
        """ Print profiling reports """

        print("Writing lpprof performance summary to : {}/LPprof_perf_report".format(self.traces_directory))

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
            if metric_type in ['asm','sym','vectorization']:
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
                    


            
        
