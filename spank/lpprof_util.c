#include "lpprof_util.h"
#include <dirent.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stddef.h>
#include <stdlib.h>

int slurm_getenv(spank_t sp,char* value,char* env_varname){

  char error_msg[512];
  snprintf(error_msg,512,"Cannot get %s",env_varname);
  
  if (spank_getenv (sp,env_varname, value, SLURM_ENVSIZE)
      != ESPANK_SUCCESS){
    return (-1);
  }
  return(0);
}

int write_pid_file(pid_t pid){
  // Make a file named with current task pid
  char s_pid[64];   // 64 digits for pid should be enought
  snprintf(s_pid, 1024, "%d",pid);
  FILE* pidfile=fopen(s_pid,"w");
  fclose(pidfile);

}

int count_pid_files(){

  int count=0;
  int len_entry=0;
  DIR * dir=NULL;
  struct dirent * buf=NULL, * de=NULL;

  
  if ((dir = opendir("."))
      && (len_entry = offsetof(struct dirent, d_name) + fpathconf(dirfd(dir), _PC_NAME_MAX) + 1)
      && (buf = (struct dirent *) malloc(len_entry)))
    {
      while (readdir_r(dir, buf, &de) == 0 && de)
	{
	  if (de->d_type == DT_REG)
	    {
	      count+=1;
	    }
	}
    }
  
  free(buf);


  return count;
}


int read_pids(char** pid_list){

  int first=1;
  int len_entry=0;
  DIR * dir=NULL;
  struct dirent * buf=NULL, * de=NULL;

  
  if ((dir = opendir("."))
      && (len_entry = offsetof(struct dirent, d_name) + fpathconf(dirfd(dir), _PC_NAME_MAX) + 1)
      && (buf = (struct dirent *) malloc(len_entry)))
    {
      while (readdir_r(dir, buf, &de) == 0 && de)
	{
	  if (de->d_type == DT_REG)
	    {
	      if(first){
		first=0;
	      }else{
		strcat(*pid_list,",");
	      }
	      strcat(*pid_list,de->d_name);
	      
	    }
	}
    }
  else{
    return(-1);
  }
  
  free(buf);

  return(0);

}
