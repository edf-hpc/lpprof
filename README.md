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

### Percentage of cycles spent in page table walking caused by TLB miss

This metric uses hardware counters that are available on modern Intel
CPU at least from Sandy-Bridge to Kaby-Lake architectures.
It is computed as the following ratio :

~~~
(ITLB_MISSES.WALK_DURATION + DTLB_MISSES.WALK_DURATION)*100 / cycles
~~~


### Floating point SSE,AVX,AVX(2) instructions proportion

SSE, AVX and AVX2 proportion and vectorisation ratio are computed from assembly instructions samples.

### Symbols representing 95% of collected samples

Table of occurence rate of symbols.

## Example

Profiling of High Performance Linpack:

~~~
lpprof -launcher=srun -frequency=1000 ./xhpl
~~~

It gives the following results per core:

~~~
Elapsed time: 145.84s
-------------------------------------------------------
Instructions per cycle: 3.13
-------------------------------------------------------
Percentage of cycles spent in page table walking caused by TLB miss: 0.06%
-------------------------------------------------------
Floating point instructions summary :

    Percentage of floating point scalar instructions:        0.00 %
    Percentage of floating point SSE packed instructions:    0.00 %
    Percentage of floating point AVX instructions:           5.68 %
    Percentage of floating point AVX2 instructions:          94.32 %


-------------------------------------------------------

Table below shows the top 95% of assembly instructions occurence rate in collected samples, samples were collected at a 1000Hz frequency:
-------------------------------------------------------
|   proportion  | occurence |     asm_instruction     |
-------------------------------------------------------
|41.12%         |58467      |vfmadd231pd              |
|17.87%         |25412      |vmovupd                  |
|13.04%         |18545      |vbroadcastsd             |
|6.97%          |9909       |prefetcht0               |
|5.12%          |7282       |mov                      |
|2.12%          |3011       |sub                      |
|2.08%          |2951       |vmulpd                   |
|1.59%          |2259       |add                      |
|1.56%          |2224       |unknown                  |
|1.32%          |1877       |cmp                      |
|0.74%          |1050       |test                     |
|0.69%          |988        |je                       |
|0.49%          |702        |vxorpd                   |
|0.46%          |654        |cmpl                     |
-------------------------------------------------------


Table below shows the top 95% of symbols occurence rate in collected samples, samples were collected at a 1000Hz frequency:
----------------------------------------------------------------------------
|   proportion  | occurence |           symbol                              |
----------------------------------------------------------------------------
|81.95%         |114698     |mkl_blas_avx2_dgemm_kernel_0                   |
|5.68%          |7947       |PMPIDI_CH3I_Progress                           |
|2.34%          |3282       |mkl_blas_avx2_dgemm_dcopy_down12_ea            |
|1.38%          |1933       |HPL_lmul                                       |
|1.12%          |1570       |mkl_blas_avx2_dtrsm_kernel_ru_0                |
|0.86%          |1210       |mkl_blas_avx2_dgemm_dcopy_down4_ea             |
|0.82%          |1148       |copy_user_enhanced_fast_string                 |
|0.69%          |964        |HPL_rand                                       |
|0.68%          |956        |HPL_ladd                                       |
----------------------------------------------------------------------------
~~~
