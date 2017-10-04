/*
*   To compile:
*    gcc -shared -o lpprof.so lpprof.c
*
*/
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/resource.h>
#include <slurm/spank.h>
#include <linux/limits.h>

/*
* All spank plugins must define this macro for the
* Slurm plugin loader.
*/

SPANK_PLUGIN(lpprof, 1);


#define LPPROF_ENV_VAR "SLURM_LPPROF"
#define FREQUENCY_NOT_SET -1
#define SLURM_ENVSIZE 8192

static int frequency=FREQUENCY_NOT_SET;
static int profiled_task=0;

static int _exec_lpprof(spank_t sp,int frequency,int rank,
			const char* slurm_submit_dir,
			const char* slurm_job_id,
			const char* slurm_env_path);

static int _lpprof_opt_process (int val,
				const char *optarg,
				int remote);

static int _slurm_getenv(spank_t sp,char* value,char* env_varname);


/*
 *  Provide a --lpprof=[frequency] option to srun:
 */
struct spank_option spank_options[] =
  {
    { "lpprof", "[frequency]",
      "Profile run using perf sampling at [frequency]Hz.", 2, 0,
      (spank_opt_cb_f) _lpprof_opt_process
    },
    SPANK_OPTIONS_TABLE_END
  };


static int _slurm_getenv(spank_t sp,char* value,char* env_varname){

  char error_msg[512];
  snprintf(error_msg,512,"Cannot get %s",env_varname);
  
  if (spank_getenv (sp,env_varname, value, SLURM_ENVSIZE)
      != ESPANK_SUCCESS){
    return (-1);
  }
  return(0);
}

int slurm_spank_task_exit(spank_t sp, int ac, char **av)
{

  if(frequency==FREQUENCY_NOT_SET){
    return(0);
  }

  int taskid,taskpid;
  spank_get_item (sp, S_TASK_ID, &taskid);
  
  //TODO Find a cleaner way to wait for lpprof to finish
  if (taskid==profiled_task){
    slurm_verbose("Wait 10 seconds for lpprof summary to be written");
    sleep(10);
  }
  
  return(0);
}


int slurm_spank_task_init (spank_t sp, int ac, char **av)
{

  if(frequency==FREQUENCY_NOT_SET){
    return(0);
  }
  
  unsigned int globalid;
  int taskid;
  char slurm_submit_dir[PATH_MAX];
  char slurm_job_id [SLURM_ENVSIZE];
  char slurm_env_path [SLURM_ENVSIZE];
  char slurm_step_num_tasks [SLURM_ENVSIZE];
  
  _slurm_getenv(sp,slurm_submit_dir,"SLURM_SUBMIT_DIR");
  _slurm_getenv(sp,slurm_job_id,"SLURM_JOB_ID");
  _slurm_getenv(sp,slurm_env_path,"PATH");

  // If NUM_TASKS is not set current process is the parent slurmstepd process
  // that should not be profiled.
  if(_slurm_getenv(sp,slurm_step_num_tasks,"SLURM_STEP_NUM_TASKS"))
    return (0);

  spank_get_item (sp, S_TASK_ID, &taskid);
  spank_get_item (sp, S_TASK_GLOBAL_ID, &globalid);

  // Execute lpprof profiler on selected tasks
  if (taskid==profiled_task){
    if(_exec_lpprof(sp,frequency,taskid,slurm_submit_dir,slurm_job_id,slurm_env_path)){
      slurm_error("Error with srun --lpprof spank plugin option : %m ");
      return (-1);
    }
  }
  
  return (0);
}



static int _exec_lpprof(const spank_t sp,int frequency,int rank,
			const char* slurm_submit_dir,
			const char* slurm_job_id,
			const char* slurm_env_path){

  char output_dir[PATH_MAX];
  int pid=getpid();

  // Create a child process profiling the parent
  pid_t lpprof_pid=fork();
  switch (lpprof_pid) {
  case -1:
    slurm_error("lpprof fork : %m ");
    return(-1);
  case 0:
    snprintf(output_dir,PATH_MAX,"%s/PERF_%s",slurm_submit_dir,slurm_job_id);

    if (chdir(slurm_submit_dir)){
      slurm_error("Cannot chdir to %s : %m ",slurm_submit_dir);
      return (-1);
    }
    struct stat st = {0};
    // Make lpprof outputdir if it does not already exist
    if (stat(output_dir, &st) == -1) {
      if (mkdir(output_dir,S_IXUSR|S_IWUSR|S_IRUSR)){
	slurm_error("Cannot mkdir %s : %m ",output_dir);
	return (-1);
      }
    }

    char s_pid[1024];
    char s_frequency[1024];
    char s_rank[1024];
    snprintf(s_pid, 1024, "%d",pid);
    snprintf(s_frequency, 1024, "%d", frequency);
    snprintf(s_rank, 1024, "%d", rank);

    setenv("PATH", slurm_env_path, 1);
    execvp("lpprof" ,(char *[]){"lpprof","-pid",s_pid,"-frequency",s_frequency, 
	  "-rank",s_rank,"-o",output_dir, NULL});
    
    slurm_error("execv : %m ");
    return(-1);
  default:
    return(0);
  }
}

static int _lpprof_opt_process (int val,
				const char *optarg,
				int remote)
{
    
  if (optarg == NULL) {
    slurm_error ("frequency: invalid argument");
    return (-1);
  }
  
  if ((atoi (optarg) <= 0 )&&(atoi(optarg) != FREQUENCY_NOT_SET)) {
    slurm_error ("Bad value for --lpprof frequency: %s ",
		 optarg);
    return (-1);
  }

  frequency=atoi(optarg);

  return (0);
}
