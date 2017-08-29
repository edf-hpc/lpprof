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
import sys, re, os, io
        
class ValgrindMemoryProfiler :
    """ Valgrind massif memory profiling, it makes the profiled programm runs slowly. """

    def __init__(self,trace_file,output_files=None):
        self.trace_file=trace_file
        
        if output_files:
            self.output_files=output_files
        else:
            self.output_files=[self.trace_file]

        self.graph=''
            
    @property
    def global_metrics(self):
        """ Return a dictionnary with metrics that could be used outside this pofiler """
        return {}
        
    
    def get_profile_cmd(self):
        """ Valgrind memory profiling command """
        
        return "valgrind --trace-children=yes --tool=massif --pages-as-heap=yes --massif-out-file={} ".format(self.trace_file)

    
    def analyze(self):
        """ Sum hardware counters over evry output file and compute the mean. """

        ms_print_cmd="ms_print {}".format(self.output_files[0])
        ms_print_process=Popen(ms_print_cmd,shell=True, stdout=PIPE,stderr=PIPE)
        stdout,stderr=ms_print_process.communicate()
        ms_print_output=io.StringIO(stdout.decode('utf8'))
        
        
        for line in ms_print_output:
            self.graph+=line
                    

    def report(self):
        """ Standard global reporting method """
        for graphline in io.StringIO(self.graph):
            print(graphline)
            

        
            
