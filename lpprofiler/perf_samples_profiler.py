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
import lpprofiler.profiler as prof
import lpprofiler.metrics_manager as metpm
import sys, re, os, io
import operator

        
class PerfSamplesProfiler(prof.Profiler) :

    def __init__(self,trace_file,metrics_manager,output_files=None,profiling_args=None):
        """ Constructor """
        
        prof.Profiler.__init__(self, trace_file,metrics_manager,output_files,profiling_args)

        if "frequency" in self.profiling_args:
            self.frequency=self.profiling_args["frequency"]
        else:
            self.frequency="99"

        # This dictionnary fasten assembly instruction decoding from address by
        # keeping assembly instructions for adress that have already been decoded.
        self.known_assembly_dic = {}

        # Store starting addresses of binaries mapped into the virtual addres space of the main process
        self.binary_mapping = {}

        
    def get_profile_cmd(self,pid=None):
        """ Assembly instructions profiling command """
        if pid:
            return "perf record -g --pid={} -F {} -o {} ".format(pid,self.frequency,self.trace_file)
        else:
            return "perf record -g -F {} -o {} ".format(self.frequency,self.trace_file)

    def analyze(self):
        """ Count assembly instructions and symbols """
        self._analyze_perf_samples()
                
        if "flame_graph" in self.profiling_args:
            print("Build flame Graph")
            self._build_flame_graph()

    def report(self):
        """ Standard global reporting method """
        pass

    def _read_mmap_table(self,output_file):
        """ Fill a dictionary with binary mappings read from perf samples """

        perf_cmd="perf script -i {} --show-mmap-events | grep -i 'PERF\_RECORD\_MMAP'".format(output_file)

        perf_process=Popen(perf_cmd,shell=True, stdout=PIPE,stderr=PIPE)            
        stdout,stderr=perf_process.communicate()
        raw_mmap=io.StringIO(stdout.decode('utf-8'))

        # Reset binary mapping
        self.binary_mapping={}

        for mapline in raw_mmap:
            if 'PERF_RECORD_MMAP' in mapline:
                binary=mapline.split(' ')[-1].rstrip()
                m = re.match(r"^.*\[(\w+)\(",mapline)
                start_address=m.group(1)
                self.binary_mapping[binary]=start_address                    

    def _get_perf_script_output(self,output_file,perf_options="-G -f ip,sym,dso"):
        """ Call perf script and analyze profiling output files"""
        perf_output=''
        
        perf_cmd="perf script -i {} {}".format(output_file,perf_options)

        perf_process=Popen(perf_cmd,shell=True, stdout=PIPE,stderr=PIPE)
        stdout,stderr=perf_process.communicate()
        perf_output+=stdout.decode('utf-8')

        return perf_output

    def _analyze_perf_script_output_line(self,line,rank):

        m=re.match(r"\s+(\w+)\s(.*)\s\((.*)\)\s+",line)
        # Perf script output may contain empty lines
        if not m :
            return
        
        eip=m.group(1)
        sym=m.group(2)
        binary_path=m.group(3)
        asm_name='unknown'

        
        # Address from kallsyms won't be analyzed
        if os.path.exists(binary_path):
            if (binary_path+eip) in self.known_assembly_dic:
                asm_name=self.known_assembly_dic[binary_path+eip] 
            else:
                start_address='0x0'
                if (binary_path in self.binary_mapping) and\
                   ('.so' in binary_path or '.ko' in binary_path): 
                    # check for .so or .ko cause main binary do not need to be vma adjusted
                    start_address=self.binary_mapping[binary_path]
                            
                asm_name=self.get_asm_ins(binary_path,eip,start_address)
                self.known_assembly_dic[binary_path+eip]=asm_name
            
        # Count instruction
        self.metrics_manager.add_metric(rank,'asm',asm_name,1)
        
        # Count symbols
        self.metrics_manager.add_metric(rank,'sym',sym,1)
        
        
    
    def _analyze_perf_samples(self):
        """ Count each assembly instruction occurence found in perf samples and store them
        in a dictionnary."""

        rank=0
        for output_file in self.output_files:

            asm_name="unknown"
  
            """ Read binary mappings from samples """
            self._read_mmap_table(output_file)

            """ Get instruction pointer and dynamic shared object location from samples """        
            perf_script_output = io.StringIO(self._get_perf_script_output(output_file,"-G -f ip,sym,dso"))
            # Parse each line to sum symbols and assembly instructions occurences
            for line in perf_script_output:
                self._analyze_perf_script_output_line(line,rank)

            # Extract vectorization information
            self._analyze_vectorization(rank)
            rank+=1


    def _build_flame_graph(self):
        """ Build Flame Graph from perf samples """

        for output_file in self.output_files:
            flame_cmd="perf script -i {} | stackcollapse-perf.pl | flamegraph.pl > {}/flames.svg".format(output_file,os.path.dirname(output_file))

            flame_process=Popen(flame_cmd,shell=True, stdout=PIPE,stderr=PIPE)            
            stdout,stderr=flame_process.communicate()

            #if stderr:
            #    print("Error generating FlameGraph : {} ".format(stderr.decode('utf-8')))
   
        
    def get_asm_ins(self,binary_path,eip_address,start_address="0x0"):
        """ Get assembler instruction from instruction pointer and binary path """
        
        # Objdump to dissassemble the binary matching eip
        # objdump_cmd='objdump -d --prefix-addresses --start-address={} \
        # --stop-address={} --adjust-vma={} {}' \
        #     .format(hex(int(eip_address,16)),hex(int(eip_address,16)+1),hex(int(start_address,16)),binary_path)

        adjusted_eip_address=int(eip_address,16)-int(start_address,16)

        objdump_cmd='objdump -d --prefix-addresses --start-address={} \
        --stop-address={} {}'.format(
            hex(adjusted_eip_address),hex(adjusted_eip_address+1),binary_path)
        
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




    def _analyze_vectorization(self,rank):

        """ Extract vectorization informations from asm symbols """
        
        # Compute vectorization related metrics
        total_sampled_ins=0
        flop_ins=0
        flop_scalar_ins=0
        sse_pd_ins=0
        avx_ins=0
        avx2_ins=0

        
#       for asm_name in self.assembly_instructions_counts:
        for asm_name in self.metrics_manager.get_metric_names('asm'):
            current_count=self.metrics_manager.get_metric_count('asm',asm_name,rank)
            if not current_count:
                continue

            total_sampled_ins+=current_count
                    
            # Handle x86_asm assembly
            # TODO handle non x86 assembly

            flop_ops=('add','mul','sub','div','sqrt')
            if any (op in asm_name for op in flop_ops):
                if asm_name.endswith("pd"):
                    flop_ins+=current_count
                    sse_pd_ins+=current_count
                elif asm_name.endswith("sd"):
                    flop_scalar_ins+=current_count
                    flop_ins+=current_count
                else:
                    continue

                if (asm_name.startswith("vfmadd") or
                    asm_name.startswith("vfnmadd")):
                    avx2_ins+=current_count
                    if asm_name.endswith("pd"):
                        sse_pd_ins-=current_count
                    if asm_name.endswith("sd"):
                        flop_scalar_ins-=current_count
                elif asm_name.startswith("v"):
                    avx_ins+=current_count
                    if asm_name.endswith("pd"):
                        sse_pd_ins-=current_count
                    if asm_name.endswith("sd"):
                        flop_scalar_ins-=current_count

        if(flop_ins):
            metric_type='vectorization'
            self.metrics_manager.add_metric(rank,metric_type,"flop_scalar_prop",
                                            (flop_scalar_ins/flop_ins)*100)
            self.metrics_manager.add_metric(rank,metric_type,"sse_pd_prop",
                                            (sse_pd_ins/flop_ins)*100)
            self.metrics_manager.add_metric(rank,metric_type,"avx_prop",
                                            (avx_ins/flop_ins)*100)
            self.metrics_manager.add_metric(rank,metric_type,"avx2_prop",
                                            (avx2_ins/flop_ins)*100)


    # def _report_assembly_usage(self) :
    #     """ Print assembly instruction sorted by occurences counts in descending order """

    #     sorted_asm_list=sorted(self.assembly_instructions_counts.items(),\
    #                            key=operator.itemgetter(1),reverse=True)
    #     sum_asm_occ=sum(asm_el[1] for asm_el in sorted_asm_list)

    #     tot_prop=0
    #     prop_threshold=95
    #     result=''
        

    #     result+="\nTable below shows the top {}% of assembly instructions occurence rate in collected samples, samples were collected at a {}Hz frequency:\n".format(prop_threshold,self.frequency)
    #     result+="-------------------------------------------------------\n"
    #     result+="|   proportion  | occurence |     asm_instruction     |\n"
    #     result+="-------------------------------------------------------\n"
    #     # Print untill a total proportion of 95% of total asm instructions is reached
    #     for asm_el in sorted_asm_list :
    #         prop_asm=(float(asm_el[1])/sum_asm_occ)*100
    #         tot_prop+=prop_asm
    #         result+='|'+'{:.2f}%'.format(prop_asm).ljust(15)+'|'+str(asm_el[1]).ljust(11)+'|'+asm_el[0].ljust(25)+'|\n'
    #         if(tot_prop>prop_threshold):
    #             break
            
    #     result+="-------------------------------------------------------\n"
        
    #     return result


    # def _report_symbols_usage(self) :
    #     """ Print assembly instruction sorted by occurences counts in descending order """

    #     sorted_symbols_list=sorted(self.symbols_counts.items(),\
    #                            key=operator.itemgetter(1),reverse=True)
    #     sum_symbols_occ=sum(sym_el[1] for sym_el in sorted_symbols_list)
    #     maxlen_symbols=max(len(sym_el[0]) for sym_el in sorted_symbols_list)
        
    #     # Avoid multilines print by limiting symbol length
    #     maxlen_symbols=min(130,maxlen_symbols);

    #     tot_prop=0
    #     prop_threshold=95
    #     result=''
    #     result+="\nTable below shows the top {}% of symbols occurence rate in collected samples, samples were collected at a {}Hz frequency:\n".format(prop_threshold,self.frequency)
    #     result+="\n".rjust(30+maxlen_symbols,'-')
    #     result+="|   proportion  | occurence |         symbol    ".ljust(29+maxlen_symbols)+"|\n"
    #     result+="\n".rjust(30+maxlen_symbols,'-')
    #     # Print untill a total proportion of 95% of total asm instructions is reached
    #     for sym_el in sorted_symbols_list :
    #         prop_sym=(float(sym_el[1])/sum_symbols_occ)*100
    #         tot_prop+=prop_sym
    #         result+='|'+'{:.2f}%'.format(prop_sym).ljust(15)+'|'+str(sym_el[1]).ljust(11)+'|'+sym_el[0].ljust(maxlen_symbols)+'|\n'
    #         if(tot_prop>prop_threshold):
    #             break
            
    #     result+="\n".rjust(30+maxlen_symbols,'-')
        
    #     return result

