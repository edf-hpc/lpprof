# LPprof

Lightweight Performance profiler using Linux perf_events.
It combines *perf record* samples and *perf stat* hardware counters to provide raw and derived metrics.

LPprof simplifies the use of perf with srun parallel launcher. It can also be used to profile a processus given its pid. In both cases it provides a performance summary with the following items:

## Metrics

### Assembly instructions representing 95% of collected samples

Table of occurence rate of assembly instructions.
Assembly instructions reported correspond to instruction pointer addresses found in perf samples.

### Elapsed time

cpu-clock hardware counter.

### Instructions per cycle

ins-per-cycle hardware counter.

### Estimated Gflops per core

Gflops are estimated by combining instructions per cycle and mean flop
per instruction.
Mean floating point per instruction is computed from assembly
instructions found in samples.

### Floating point AVX(2) instructions proportion and floating point operations vectorisation ratio

AVX and AVX2 proportion and vectorisation ratio are computed from
assembly instructions samples.

### Percentage of cycles spent in page table walking caused by TLB miss

This metric uses hardware counters that are available on modern Intel
CPU at least from Sandy-Bridge to Kaby-Lake architectures.
It is computed as the following ratio : (ITLB_MISSES.WALK_DURATION +
DTLB_MISSES.WALK_DURATION)*100 / cycles

### Estimated MPI communication time

Elapsed time mutltiplied by occurence rate of libmpi.so samples.


## Example

Profiling of High Performance Linpack:

~~~
lpprof -launcher="srun --cpu_bind=cores,verbose --distribution=block:block" -frequency="99" ./xhpl
~~~

It gives the following results per core:

~~~
-------------------------------------------------------
Elapsed time: 58.43s
-------------------------------------------------------
Instructions per cycle: 2.74
-------------------------------------------------------
Estimated Gflops per core: 23.83 Gflops
-------------------------------------------------------
Percentage of floating point AVX instructions: 37.50 %
Percentage of floating point AVX2 instructions: 62.50 %
Floating point operations vectorisation ratio: 100.00 %
-------------------------------------------------------
Percentage of cycles spent in page table walking caused by TLB miss: 0.03 %
-------------------------------------------------------
Estimated MPI communication time: 5.08 %
-------------------------------------------------------

Table below shows the top 95% of assembly instructions occurence rate in collected samples, samples were collected at a 99Hz frequency:
-------------------------------------------------------
|   proportion  | occurence |     asm_instruction     |
-------------------------------------------------------
|41.43%         |4095       |vfmadd231pd              |
|18.44%         |1823       |vmovupd                  |
|11.75%         |1161       |vbroadcastsd             |
|5.21%          |515        |mov                      |
|4.54%          |449        |prefetcht0               |
|3.11%          |307        |prefetchnta              |
|2.25%          |222        |sub                      |
|2.20%          |217        |add                      |
|1.57%          |155        |vmulpd                   |
|1.18%          |117        |cmp                      |
|0.91%          |90         |vaddpd                   |
|0.74%          |73         |movdqa                   |
|0.49%          |48         |test                     |
|0.39%          |39         |cmpl                     |
|0.33%          |33         |lea                      |
|0.32%          |32         |vfnmadd231pd             |
|0.32%          |32         |vfnmadd213pd             |
-------------------------------------------------------
~~~
