
#ifndef LPPROF_H_
#define LPPROF_H_



#include <stdlib.h>
#include <string.h>
#include "lpprof_util.h"

static int frequency=FREQUENCY_NOT_SET;
static char* rank_list=NULL;

static int _exec_lpprof(spank_t sp,int frequency,
			const char* slurm_submit_dir,
			const char* slurm_job_id,
			const char* slurm_env_path,
			char* pid_list);

static int _lpprof_opt_process (int val,
				const char *optarg,
				int remote);


static int _init_lpprof_dir(unsigned int taskid,
			    unsigned int nbtasks,
			    const char* slurm_submit_dir,
			    const char* slurm_job_id,
			    const char* slurm_env_path,
			    const char* slurm_nodename,
			    char** pid_list);

#endif // LPPROF_H_
