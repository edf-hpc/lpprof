# LPprof

Lightweight Performance profiler using Linux perf_events.
It combines *perf record* samples and *perf stat* hardware counters to provide raw and derived metrics.

LPprof simplifies the use of perf with srun parallel launcher. It can also be used to profile a processus given its pid.


## Example

Profiling of High Performance Linpack at 99Hz :

~~~
lpprof -launcher="srun" -frequency="99" ./xhpl
~~~



## Slurm Spank plugin usage example


Profiling of ranks 0,1,2,3,4 7 of IMB-MPI1 benchmark at 99hz :

~~~
srun --lpprof_f=99 --lpprof_r=0-4,7 ./IMB-MPI1 pingpong allreduce
~~~