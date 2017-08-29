# -*- coding: utf-8 -*-
##############################################################################
#  This file is part of the LPprofiler profiling tool.                       #
#        Copyright (C) 2017  EDF SA                                          #
#                                                                            #
#  LPprofiler is free software: you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by      #
#  the Free Software Foundation, either version 3 of the License, or         #
#  (at your option) any later version.                                       #
#                                                                            #
#  LPprofiler is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#  GNU General Public License for more details.                              #
#                                                                            #
#  You should have received a copy of the GNU General Public License         #
#  along with LPprofiler.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                            #
############################################################################## 

from subprocess import Popen,PIPE
import sys
import re
import os
import io
import operator
        
class PerfSamplesProfiler :

    def __init__(self,trace_file,output_files=None):
        """ trace_file is the filename used as output to generate the profiling command. 
        Lpprofiler can adapt the original profiling command to make it write multiple output_files
        (ex: one per rank with srun). """
        
        self.trace_file=trace_file

        if output_files:
            self.output_files=output_files
        else:
            self.output_files=[self.trace_file]

        # This dictionnary fasten assembly instruction decoding from address by
        # keeping assembly instructions for adress that have already been decoded.
        self.known_assembly_dic = {}
        
        self.assembly_instructions_counts = {}

        self.mpi_samples=0

        # Store starting addresses of binaries mapped into the virtual addres space of the main process
        self.binary_mapping={}

    @property
    def global_metrics(self):
        """ Return a dictionnary with metrics that could be used outside this pofiler """
        global_metrics={}
        
        # Compute a dflop_per_ins metric
        # /!\ Sqrt is counted as mul and add

        dflop=0
        total_sampled_ins=0
        
        for asm_name in self.assembly_instructions_counts:
            current_count=self.assembly_instructions_counts[asm_name]
            total_sampled_ins+=current_count
            dflop_tmp=0

            # Handle x86_asm assembly
            # TODO handle non x86 assembly

            if asm_name.endswith("pd"):
                dflop_tmp=2
            elif asm_name.endswith("sd"):
                dflop_tmp=1
            else:
                dflop_tmp=0

            if asm_name.startswith("vfmadd"):
                dflop+=dflop_tmp*4*current_count
            elif asm_name.startswith("v"):
                dflop+=dflop_tmp*2*current_count
            else:
                dflop+=dflop_tmp*current_count
                    
        global_metrics["dflop_per_ins"]=dflop/total_sampled_ins
        global_metrics["mpi_samples_prop"]=(self.mpi_samples/total_sampled_ins)*100
        
        
        return global_metrics

        
    def get_profile_cmd(self,frequency="99"):
        """ Assembly instructions profiling command """
        return "perf record -g -F {} -o {} ".format(frequency,self.trace_file)

    def analyze(self):
        """ Standard global analyze method """
        self._analyze_perf_samples()

    def report(self):
        """ Standard global reporting method """
        self._report_assembly_usage()

    def _read_mmap_table(self):
        """ Fill a dictionary with binary mappings read from perf samples """
        for output_file in self.output_files:
            perf_cmd="perf script -i {} --show-mmap-events | grep -i 'PERF\_RECORD\_MMAP'".format(output_file)

            perf_process=Popen(perf_cmd,shell=True, stdout=PIPE,stderr=PIPE)            
            stdout,stderr=perf_process.communicate()
            raw_mmap=io.StringIO(stdout.decode('utf-8'))

            for mapline in raw_mmap:
                if 'PERF_RECORD_MMAP' in mapline:
                    binary=mapline.split(' ')[-1].rstrip()
                    m = re.match(r"^.*\[(\w+)\(",mapline)
                    start_address=m.group(1)
                    self.binary_mapping[binary]=start_address
                    

    def _get_perf_script_output(self,perf_options="-f ip,dso"):
        """ Call perf script and analyze profiling output files"""
        perf_output=''
        
        for output_file in self.output_files:
            perf_cmd="perf script -i {} {}".format(output_file,perf_options)

            perf_process=Popen(perf_cmd,shell=True, stdout=PIPE,stderr=PIPE)
            stdout,stderr=perf_process.communicate()
            perf_output+=stdout.decode('utf-8')

        return perf_output

        
    def _analyze_perf_samples(self):
        """ Count each assembly instruction occurence found in perf samples and store them
        in a dictionnary."""
        
        asm_name="unknown"

        """ Read binary mappings from samples """
        self._read_mmap_table()
        
        """ Get instruction pointer and dynamic shared object location from samples """        
        perf_script_output = io.StringIO(self._get_perf_script_output("-f ip,dso"))
        self.mpi_samples=0
        
        for line in perf_script_output:
            m=re.match(r"\s+(\w+)\s+\((.*)\)\s+",line)
            # Perf script output may contain empty lines
            if m :
                eip=m.group(1)
                binary_path=m.group(2)
                # Address from kallsyms won't be analyzed
                if os.path.exists(binary_path):
                    if (binary_path+eip) in self.known_assembly_dic:
                        asm_name=self.known_assembly_dic[binary_path+eip] 
                    else:
                        start_address=self.binary_mapping[binary_path]
                        asm_name=self.get_asm_ins(binary_path,eip,start_address)
                        self.known_assembly_dic[binary_path+eip]=asm_name

                # Count instruction
                if asm_name in self.assembly_instructions_counts:
                    self.assembly_instructions_counts[asm_name]+=1
                else:
                    self.assembly_instructions_counts[asm_name]=1

                # Count MPI lib occurence
                if "libmpi" in binary_path:
                    self.mpi_samples+=1
                
        
    def get_asm_ins(self,binary_path,eip_address,start_address="0x0"):
        """ Get assembler instruction from instruction pointer and binary path """
        
        # Objdump to dissassemble the binary matching eip
        objdump_cmd='objdump -d --prefix-addresses --start-address={} \
        --stop-address={} --adjust-vma={} {}' \
            .format(hex(int(eip_address,16)),hex(int(eip_address,16)+1),hex(int(start_address,16)),binary_path)

        objdump_process=Popen(objdump_cmd,shell=True, stdout=PIPE,stderr=PIPE)
        stdout,stderr=objdump_process.communicate()
        objdump_output=stdout.decode('utf-8')

        # Get objdump line containing the eip address
        regexp=r''+hex(int(eip_address,16))[2:]+'.*'
        try:
            first_line_matching_address=re.findall(regexp,objdump_output)[0]
        except:
            return 'unknown'

        # Extract assembly instruction and add result to a dictionnary to avoid recomputing it later
        assembly_instruction=first_line_matching_address.split()[2].rstrip()

        self.known_assembly_dic[binary_path+eip_address]=assembly_instruction
    
        return assembly_instruction

                
    def _report_assembly_usage(self) :
        """ Print assembly instruction sorted by occurences counts in descending order """

        sorted_asm_list=sorted(self.assembly_instructions_counts.items(),\
                               key=operator.itemgetter(1),reverse=True)
        sum_asm_occ=sum(asm_el[1] for asm_el in sorted_asm_list)

        tot_prop=0

        print()
        print("Assembly instructions representing 95% of collected samples :")
        print("-------------------------------------------------------")
        print("|   proportion  | occurence |     asm_instruction     |")
        print("-------------------------------------------------------")
        # Print untill a total proportion of 95% of total asm instructions is reached
        for asm_el in sorted_asm_list :
            prop_asm=(asm_el[1]/sum_asm_occ)*100
            tot_prop+=prop_asm
            print('|'+'{:.2f}%'.format(prop_asm).ljust(15)+'|'+str(asm_el[1]).ljust(11)+'|'+asm_el[0].ljust(25)+'|')
            if(tot_prop>95):
                break
            
        print("-------------------------------------------------------")
