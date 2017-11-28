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

int count_ranks(const char* rank_list){
  int istr;
  int current_rank=-1;
  int nbranks=0;
  char *str1,*str2,*token,*subtoken;
  char *saveptr1,*saveptr2;

  // Use a copy of initial rank_list string for parsing
  char* rank_listw=(char *) malloc(sizeof(char)*strlen(rank_list));
  strncpy(rank_listw,rank_list,strlen(rank_list));
    
  // Count number of ranks inside formated lists like : 0,2,5-7,9  
  for (istr = 1, str1 = rank_listw; ;istr++,str1=NULL) {
    current_rank=-1;
    token = strtok_r(str1,",", &saveptr1);
    slurm_error("Tok1: %s",str1);
    if (token == NULL)
      break;
    for (str2 = token; ; str2 = NULL) {
      subtoken = strtok_r(str2,"-", &saveptr2);
      if (subtoken == NULL){
	slurm_error("Tok2 NULL: %s",token);
	if (current_rank>0)
	    nbranks+=1;
	break;
      }
      if (current_rank!=-1){
	if(atoi(subtoken)-current_rank>0)
	  nbranks+=atoi(subtoken)-current_rank;
	current_rank=-1;
      }else{
	current_rank=atoi(subtoken);
      }
      slurm_error("Tok2: %s",subtoken);
    }
  }

  free(rank_listw);
  return nbranks;
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
