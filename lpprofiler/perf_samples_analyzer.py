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

        
class PerfSamplesAnalyzer :

    def __init__(self,input_file):
        self._input_file=input_file
        self._known_assembly_dic = {}
        self._assembly_instructions_counts ={}


    def _get_perf_script_output(self,perf_options="-f ip,dso"):
        """ Call perf script and analyze output """        
        perf_cmd="perf script -i {} {}".format(self._input_file,perf_options)
        
        perf_process=Popen(perf_cmd,shell=True, stdout=PIPE,stderr=PIPE)
        stdout,stderr=perf_process.communicate()
        perf_output=stdout.decode('utf-8')

        return perf_output

        
    def analyze_perf_samples(self):
        """ Count each assembly instruction occurence found in perf samples and store them
        in a dictionnary."""
        
        asm_name="unknown"
        
        """ Get instruction pointer and dynamic shared object location from samples """        
        perf_script_output = io.StringIO(self._get_perf_script_output("-f ip,dso"))

        
        for line in perf_script_output:
            m=re.match(r"\s+(\w+)\s+\((.*)\)\s+",line)
            # Perf script output may contain empty lines
            if m :
                eip=m.group(1)
                binary_path=m.group(2)
                # Address from kallsyms won't be analyzed
                if os.path.exists(binary_path):
                    if (binary_path+eip) in self._known_assembly_dic:
                        asm_name=self._known_assembly_dic[binary_path+eip] 
                    else:
                        asm_name=self.get_asm_ins(binary_path,eip)
                        self._known_assembly_dic[binary_path+eip]=self.get_asm_ins(binary_path,eip)

            # Count instruction
            if asm_name in self._assembly_instructions_counts:
                self._assembly_instructions_counts[asm_name]+=1
            else:
                self._assembly_instructions_counts[asm_name]=1
            
        
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
        assembly_instruction=first_line_matching_address.split()[2]

        self._known_assembly_dic[binary_path+eip_address]=assembly_instruction
    
        return assembly_instruction

        
        
        
    def report_assembly_usage(self) :
        for asm in self._assembly_instructions_counts :
            print('asm instruction : {} occurence: {}'.format(asm,self._assembly_instructions_counts[asm]))


            
