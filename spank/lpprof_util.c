#include "lpprof_util.h"
#include <dirent.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stddef.h>
#include <stdlib.h>


void quicksort( int a[], int l, int r)
{
  int j;

  if( l < r )
    {
      // divide and conquer
      j = partition( a, l, r);
      quicksort( a, l, j-1);
      quicksort( a, j+1, r);
    }

}

int partition( int a[], int l, int r) {
  int pivot, i, j, t;
  pivot = a[l];
  i = l; j = r+1;

  while( 1)
    {
      do ++i; while( a[i] <= pivot && i <= r );
      do --j; while( a[j] > pivot );
      if( i >= j ) break;
      t = a[i]; a[i] = a[j]; a[j] = t;
    }
  t = a[l]; a[l] = a[j]; a[j] = t;
  return j;
}



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
  snprintf(s_pid, 64, "%d",pid);
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
  char* rank_listw=(char *) malloc(sizeof(char)*strlen(rank_list)+1);
  strncpy(rank_listw,rank_list,strlen(rank_list)+1);

    
  // Count number of ranks inside formated lists like : 0,2,5-7,9  
  for (istr = 1, str1 = rank_listw; ;istr++,str1=NULL) {
    current_rank=-1;
    token = strtok_r(str1,",", &saveptr1);
    if (token == NULL)
      break;
    for (str2 = token; ; str2 = NULL) {
      subtoken = strtok_r(str2,"-", &saveptr2);
      if (subtoken == NULL){
	if (current_rank>0){
	    nbranks+=1;
	}
	break;
      }
      if (current_rank!=-1){
	if(atoi(subtoken)-current_rank>0){
	  nbranks+=atoi(subtoken)-current_rank+1;
	}
	current_rank=-1;
      }else{
	current_rank=atoi(subtoken);
      }
    }
  }


  free(rank_listw);
  return nbranks;
}


int read_pids(char** pid_list,int nbpids){

  int first=1;
  int len_entry=0;
  DIR * dir=NULL;
  struct dirent * buf=NULL, * de=NULL;
  int ipid=0;
  int* ipid_list=(int*) malloc(nbpids*sizeof(int));
  
  
  if ((dir = opendir("."))
      && (len_entry = offsetof(struct dirent, d_name) + fpathconf(dirfd(dir), _PC_NAME_MAX) + 1)
      && (buf = (struct dirent *) malloc(len_entry)))
    {
      while (readdir_r(dir, buf, &de) == 0 && de)
	{
	  if (de->d_type == DT_REG)
	    {
	      ipid_list[ipid]=atoi(de->d_name);
	      ipid+=1;
	    }
	}
    }
  else{
    return(-1);
  }

  quicksort(ipid_list,0,nbpids-1);

  char pid_buffer[64]; // 64 should be enought to contain a pid
  for(ipid=0;ipid<nbpids;ipid++){
    snprintf(pid_buffer,64, "%d", ipid_list[ipid]);
    strcat(*pid_list,pid_buffer);
    if (ipid!=nbpids-1)
      strcat(*pid_list,",");
  }
  
  
  free(ipid_list);
  free(buf);

  return(0);

}
