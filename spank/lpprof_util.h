

#ifndef LPPROF_UTIL_H_
#define LPPROF_UTIL_H_

#include <slurm/spank.h>
#include <unistd.h>

#define LPPROF_ENV_VAR "SLURM_LPPROF"
#define FREQUENCY_NOT_SET -1
#define SLURM_ENVSIZE 8192

void quicksort( int a[], int l, int r);
int partition( int a[], int l, int r);
int slurm_getenv(spank_t sp,char* value,char* env_varname);
int write_pid_file(pid_t pid);
int count_pid_files();
int read_pids(char** pid_list,int nbpids);

#endif // LPPROF_UTIL_H_
