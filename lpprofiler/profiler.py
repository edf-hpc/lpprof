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
import lpprofiler.metrics_manager as metm
import sys,re,os,io
import operator
        
class Profiler :

    def __init__(self,metrics_manager,trace_files,output_files=[],profiling_args={}):
        """ trace_file is the filename used as output to generate the profiling command. 
        Lpprofiler can adapt the original profiling command to make it write multiple output_files
        (ex: one per rank with srun). """
        
        self.trace_files=trace_files

        if output_files:
            self.output_files=output_files
        else:
            self.output_files=self.trace_files

        self.profiling_args=profiling_args

        self.metrics_manager=metrics_manager

    def get_profile_cmd(self,pid=None,rank=None):
        """ Return profiling command """
        return ""

    def analyze(self):
        """ Standard analyze method """
        pass
