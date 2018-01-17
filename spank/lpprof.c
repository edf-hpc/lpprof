/*
*   To compile:
*   gcc -shared -fPIC -o lpprof.so lpprof.c lpprof_util.c
*
*/
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/resource.h>
#include <slurm/spank.h>
#include <signal.h>
#include <linux/limits.h>
#include <stdio.h>
#include <math.h>
#include "lpprof.h"

/*
* All spank plugins must define this macro for the
* Slurm plugin loader.
*/

SPANK_PLUGIN(lpprof, 1);

static int _lpprof_freq_process(int val,
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

static int _lpprof_ranks_process(int val,
				 const char *optarg,
				 int remote)
{

  rank_list=(char *) malloc(sizeof(char)*(strlen(optarg)+1));
  strncpy(rank_list,optarg,strlen(optarg)+1);

  return(0);
}



/*
 *  Provide a --lpprof=[frequency] option to srun:
 */
struct spank_option spank_options[] =
  {
    { "lpprof_f", "[frequency]",
      "Profile run using perf sampling at [frequency]Hz.", 2, 0,
      (spank_opt_cb_f) _lpprof_freq_process
    },
    { "lpprof_r", "ranks_list",
      "Profile only ranks in ranks_list. ex: -lpprof_r=0,3-7,9 ", 2, 0,
      (spank_opt_cb_f) _lpprof_ranks_process
    },
    SPANK_OPTIONS_TABLE_END
  };



int slurm_spank_task_exit(spank_t sp, int ac, char **av)
{

  if(frequency==FREQUENCY_NOT_SET){
    return(0);
  }

  int taskid=0;
  spank_get_item (sp, S_TASK_ID, &taskid);

  
    
  if((spank_context() != S_CTX_REMOTE)||(taskid!=0))
    return(0);
  else{
    slurm_verbose("In remote context !");
  }

  
  char output_dir[PATH_MAX];
  char slurm_submit_dir[PATH_MAX];
  char slurm_job_id [SLURM_ENVSIZE];
  char pid_dir[PATH_MAX];
  slurm_getenv(sp,slurm_submit_dir,"SLURM_SUBMIT_DIR");
  slurm_getenv(sp,slurm_job_id,"SLURM_JOB_ID");

  snprintf(output_dir,PATH_MAX,"%s/perf_%s",slurm_submit_dir,slurm_job_id);
  snprintf(pid_dir,PATH_MAX,"%s/perf_%s/lpprof_pid",slurm_submit_dir,slurm_job_id);

  if (chdir(output_dir)){
    slurm_error("Cannot chdir to %s : %m ",output_dir);
    return (0);
  }  

  // Make a file to signal that job is done to perf processes
  FILE* jobfile=fopen("job_done","w");
  fclose(jobfile);

  if (chdir(pid_dir)){
    slurm_error("Cannot chdir to %s : %m ",pid_dir);
    return (0);
  }  


  // Get lpprof pid
  char *s_pid=malloc(1024*sizeof(char));
  strcpy(s_pid,"");
  read_pids(&s_pid,1);
  int lpprof_pid=atoi(s_pid);

  // Wait for lpprof process to end
  struct stat sts;
  char proc_pid_file[1024];    
  snprintf(proc_pid_file,1024,"/proc/%s",s_pid);
  
  while (!(stat(proc_pid_file, &sts) == -1 && errno == ENOENT)) {
    usleep(10);
  }

  if (chdir(output_dir)){
    slurm_error("Cannot chdir to %s : %m ",output_dir);
    return (0);
  }  

  if (remove("job_done")){
    slurm_error("Cannot remove job_done : %m ");
  }

  free(s_pid);
  
  return(0);
}


int slurm_spank_task_init (spank_t sp, int ac, char **av)
{

  if(frequency==FREQUENCY_NOT_SET){
    return(0);
  }
  
  unsigned int globalid=0;
  int taskid=0;
  int nbtasks=0;
  int ismaster=0;
  char slurm_submit_dir[PATH_MAX];
  char slurm_job_id [SLURM_ENVSIZE];
  char slurm_env_path [SLURM_ENVSIZE];
  char slurm_nodename [SLURM_ENVSIZE];
  char slurm_step_num_tasks [SLURM_ENVSIZE];
  
  slurm_getenv(sp,slurm_submit_dir,"SLURM_SUBMIT_DIR");
  slurm_getenv(sp,slurm_job_id,"SLURM_JOB_ID");
  slurm_getenv(sp,slurm_env_path,"PATH");
  slurm_getenv(sp,slurm_nodename,"SLURMD_NODENAME");

  // If NUM_TASKS is not set current process is the parent slurmstepd process
  // that should not be profiled.
  if(slurm_getenv(sp,slurm_step_num_tasks,"SLURM_STEP_NUM_TASKS"))
    return (0);

  spank_get_item (sp, S_TASK_ID, &taskid);
  spank_get_item (sp, S_TASK_GLOBAL_ID, &globalid);
  spank_get_item (sp, S_JOB_TOTAL_TASK_COUNT,&nbtasks);


  // Check writing rate
  if(taskid==0){
    int size_sample=30;
    int nb_prof_ranks=nbtasks;
    if (rank_list)
      nb_prof_ranks=count_ranks(rank_list);
    
    float writing_rate=(((float)frequency*nb_prof_ranks*size_sample*60)/1000000);

    if (writing_rate>100){
      slurm_error("Collecting samples at %dHz on %d ranks would lead to write samples at %dMo per minute. Please retry with lower profiling frequency or with less ranks",frequency,nb_prof_ranks,writing_rate);
      return(-1);
    }
  }
  
  
  // Initialize a pid_list
  char *pid_list=NULL;
  pid_list=malloc(sizeof(char)*nbtasks*HOSTPID_MXSZ);
  strcpy(pid_list,"");

  
  // Init directory and pid_list
  if (_init_lpprof_dir(taskid,nbtasks,slurm_submit_dir,slurm_job_id,slurm_env_path,slurm_nodename,&pid_list)){
      slurm_error("Error with srun --lpprof spank plugin option : %m ");
      return (-1);
  }
      
  // Execute lpprof profiler from first pid
  if(taskid==0){
    if(_exec_lpprof(sp,frequency,slurm_submit_dir,slurm_job_id,slurm_env_path,pid_list)){
      slurm_error("Error with srun --lpprof spank plugin option : %m ");
      return (-1);
    }
  }
  
  free(pid_list);

  
  return (0);
}


static int _init_lpprof_dir(int taskid,
			    int nbtasks,
			    const char* slurm_submit_dir,
			    const char* slurm_job_id,
			    const char* slurm_env_path,
			    const char* slurm_nodename,
			    char** pid_list){

  char output_dir[PATH_MAX];
  char pid_dir[PATH_MAX];
  int pid=getpid();

  snprintf(output_dir,PATH_MAX,"%s/perf_%s",slurm_submit_dir,slurm_job_id);
  snprintf(pid_dir,PATH_MAX,"%s/perf_%s/pids",slurm_submit_dir,slurm_job_id);

  if (chdir(slurm_submit_dir)){
    slurm_error("Cannot chdir to %s : %m ",slurm_submit_dir);
    return (-1);
  }
  struct stat st = {0};
  // Make lpprof outputdir if it does not already exist
  if ((stat(output_dir, &st) == -1)) {
    if (mkdir(output_dir,S_IXUSR|S_IWUSR|S_IRUSR)){
      if(errno!=EEXIST){
	slurm_error("Cannot mkdir %s : %m ",output_dir);
	return (-1);
      }
    }
  }
  if (chdir(output_dir)){
    slurm_error("Cannot chdir to %s : %m ",output_dir);
    return (-1);
  }

  // Make lpprof pid dir
  if ((stat(pid_dir, &st) == -1)) {
    if (mkdir(pid_dir,S_IXUSR|S_IWUSR|S_IRUSR)){
      if(errno!=EEXIST){
	slurm_error("Cannot mkdir %s : %m ",pid_dir);
	return (-1);
      }
    }
  }
  
  if (chdir(pid_dir)){
    slurm_error("Cannot chdir to %s : %m ",pid_dir);
    return (-1);
  }
  

  write_pid_file(pid,slurm_nodename,taskid);

  // Wait for all pids to be written
  int nbpid_files_written;

  if (taskid==0){
    while(nbpid_files_written!=nbtasks)
      nbpid_files_written=count_pid_files();
  }
  
  if (taskid==0){
    if (nbpid_files_written==nbtasks){
      read_pids(pid_list,nbtasks);
    }
  }

  // Change current dir back to output dir
  if (chdir(slurm_submit_dir)){
    slurm_error("Cannot chdir to %s : %m ",output_dir);
    return (-1);
  }


  
      
  return(0);
    
}


static int _exec_lpprof(const spank_t sp,int frequency,
			const char* slurm_submit_dir,
			const char* slurm_job_id,
			const char* slurm_env_path,
			char* pid_list){

  pid_t lpprof_pid=fork();
  

  switch (lpprof_pid) {
  case -1:
    slurm_error("lpprof fork : %m ");
    return(-1);
  case 0:
    {
      char output_dir[PATH_MAX];
      char pid_dir[PATH_MAX];
      struct stat st = {0};
      snprintf(output_dir,PATH_MAX,"%s/perf_%s",slurm_submit_dir,slurm_job_id);
      
      if (chdir(output_dir)){
	slurm_error("Cannot chdir to %s : %m ",pid_dir);
	return (-1);
      }

      char s_frequency[1024];
      snprintf(s_frequency, 1024, "%d", frequency);
      setenv("PATH", slurm_env_path, 1);

      // A delay is needed to avoid the case where lpprof is unable to find threads to monitor.
      // TODO: replace sleep by a proper check.
      sleep(1);

      if(rank_list){
	execvp("lpprof" ,(char *[]){"lpprof","--pids",pid_list,"--frequency",s_frequency, 
	      "--ranks",rank_list,"-o",output_dir, NULL});
      }else{
	execvp("lpprof" ,(char *[]){"lpprof","--pids",pid_list,"--frequency",s_frequency, 
	      "-o",output_dir, NULL});
      }
    
      slurm_error("execv : %m ");
      return(-1);
    }
    
  default:
    {
      char pid_dir[PATH_MAX];
      struct stat st = {0};
      snprintf(pid_dir,PATH_MAX,"%s/perf_%s/lpprof_pid",slurm_submit_dir,slurm_job_id);

      // Make lpprof pid dir
      if (stat(pid_dir, &st) == -1) {
	if (mkdir(pid_dir,S_IXUSR|S_IWUSR|S_IRUSR)){
	  slurm_error("Cannot mkdir %s : %m ",pid_dir);
	  return (-1);
	}
      }
      
      if (chdir(pid_dir)){
	slurm_error("Cannot chdir to %s : %m ",pid_dir);
	return (-1);
      }

      // Write lpprof process pid
      write_pid_file(lpprof_pid);

      if (chdir(slurm_submit_dir)){
	slurm_error("Cannot chdir to %s : %m ",pid_dir);
	return (-1);
      }


      return(0);
    }
  }
}

