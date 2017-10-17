% lpprof(1)

# NAME

lpprof -  profiling tool

# SYNOPSIS

    lpprof [options] <cmd>


# DESCRIPTION

Lpprof combines perf record and perf stat commands on parallel processes.
It analyzes perf record samples and perf stat results to provide direct and derived metrics.

## Top 95% of assembly instructions occurence rate in collected samples
Table of occurence rate of assembly instructions.
Assembly instructions reported correspond to instruction pointer addresses found in perf samples.

## Elapsed time
cpu-clock hardware counter (perf stat).

## Instructions per cycle
ins-per-cycle hardware counter (perf stat).

## Percentage of floating point AVX(2) instructions
## and floating point operations vectorisation ratio
AVX and AVX2 proportion and vectorisation ratio are computed from assembly instructions samples.

## Percentage of cycles spent in page table walking caused by TLB miss
This metric uses hardware counters that are available on modern Intel CPU at least from Sandy-Bridge to Kaby-Lake architectures.
It is computed as the following ratio :
(ITLB_MISSES.WALK_DURATION + DTLB_MISSES.WALK_DURATION)*100 / cycles


# OPTIONS

"-launcher"
Parallel launcher (ex: srun). Use "std" to execute a program without parallel launcher.

"-launcher_args"
Launcher arguments.

"-frequency"
Frequency of perf sampling.


# SEE ALSO

perf(1)