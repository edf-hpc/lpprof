/*
*   To compile:
*    gcc -shared -o lpprof.so lpprof.c
*
*/
#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/resource.h>

#include <slurm/spank.h>

/*
* All spank plugins must define this macro for the
* Slurm plugin loader.
*/

SPANK_PLUGIN(lpprof, 1);


#define LPPROF_ENV_VAR "SLURM_LPPROF"
#define FREQUENCY_NOT_SET 99

static int frequency=FREQUENCY_NOT_SET;


static int _lpprof_opt_process (int val,
				    const char *optarg,
				    int remote);
/*
 *  Provide a --lpprof=[frequency] option to srun:
 */
struct spank_option spank_options[] =
  {
    { "lpprof", "[frequency]",
      "Profile run using perf sampling at [frequency].", 2, 0,
      (spank_opt_cb_f) _lpprof_opt_process
    },
    SPANK_OPTIONS_TABLE_END
  };



int slurm_spank_task_post_fork (spank_t sp, int ac, char **av)
{
  pid_t pid;
  int taskid;
  char val [1024];

  if (spank_getenv (sp, LPROF_ENV_VAR, val, 1024)
      != ESPANK_SUCCESS)
      return (0);

  
  spank_get_item (sp, S_TASK_GLOBAL_ID, &taskid);
  spank_get_item (sp, S_TASK_PID, &pid);

  
  
  // Execute lpprof profiler on each task
  if(_exec_lpprof(pid,frequency,rank)){
    slurm_error("--lpprof : %m ");
    return (-1);
  }

  return (0);
}


static int _exec_lpprof(int pid,int frequency,int rank){
  char lpprof_cmd[256];
  
  sprintf(lpprof_cmd,"lpprof -pid %d -frequency %d -rank",pid,frequency,rank);
  execve(lpprof_cmd,NULL,NULL);
}


static int _lpprof_opt_process (int val,
				const char *optarg,
				int remote)
{
  if (optarg == NULL) {
    slurm_error ("frequency: invalid argument!");
    return (-1);
  }


  

  if ( atoi (optarg) <= 0) {
    
    slurm_error ("Bad value for --lpprof frequency: %s",
		 optarg);
    return (-1);
  }

  frequency=atoi(optarg);

  return (0);
}
