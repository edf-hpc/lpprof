% lpprof(1)

# NAME

lpprof -  profiling tool

# SYNOPSIS

    lpprof [--launcher {std,srun} |--pids <pid_list>] [-ranks <rank_list>] [-frequency <freq>] [-o <output_dir>] <cmd>


# DESCRIPTION

Lpprof combines perf record and perf stat commands on parallel processes.
It analyzes perf record samples and perf stat results to provide direct and derived metrics in a report built when execution of the profiled
command ends. The report can be found by default in perf_\<date|slurm_job_id\>/LPprof_perf_report.

# OPTIONS

"--version"
Print lpprof version.

"--launcher"
Parallel launcher (ex: srun). Use "std" to execute a program without parallel launcher.

"--pids"
List of pids to attach to.
The pid list can be \<pid1,pid2,pid3,.....\> if alls pids are on local host or \<rank1:hostname1:pid1,rank2,hostname2,pid2,...\> if tasks are spread among different hosts.


"--frequency"
Frequency of perf sampling.

"--ranks"
List of ranks to profile (ex: --ranks 0-7,12 to profile ranks 0 to 7 and rank 12).

"-o"
Output directory, default is perf_\<slurm_job_id\> or perf_\<date> if not in a slurm allocation.


# SEE ALSO

perf(1)