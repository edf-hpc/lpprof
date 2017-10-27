# LPprof

Lightweight Performance profiler using Linux perf_events.
It combines *perf record* samples and *perf stat* hardware counters to provide raw and derived metrics.

LPprof simplifies the use of perf with srun parallel launcher. It can also be used to profile a processus given its pid. In both cases it provides a performance summary with the following items:


## Example

Profiling of High Performance Linpack:

~~~
lpprof -launcher="srun --cpu_bind=cores,verbose --distribution=block:block" -frequency="99" ./xhpl
~~~
