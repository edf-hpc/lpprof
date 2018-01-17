% lpprof(1)

# NAME

lpprof -  profiling tool

# SYNOPSIS

    lpprof [--launcher {std,srun} |--pids <pid_list>] [-ranks <rank_list>] [-frequency <freq>] [-o <output_dir>] <cmd>


# DESCRIPTION

Lpprof combines perf record and perf stat commands on parallel processes.
It analyzes perf record samples and perf stat results to provide direct and derived metrics.

# OPTIONS

"--launcher"
Parallel launcher (ex: srun). Use "std" to execute a program without parallel launcher.

"--pids"
List of pids to attach to.

"--frequency"
Frequency of perf sampling.

"--ranks"
List of ranks to profile (ex: --ranks 0-7,12 to profile ranks 0 to 7 and rank 12).

"-o"
Output directory, default is perf_<date>.


# SEE ALSO

perf(1)