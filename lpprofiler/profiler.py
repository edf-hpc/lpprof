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
        
class Profiler :

    def __init__(self,trace_file,output_files=None,profiling_args={}):
        """ trace_file is the filename used as output to generate the profiling command. 
        Lpprofiler can adapt the original profiling command to make it write multiple output_files
        (ex: one per rank with srun). """
        
        self.trace_file=trace_file

        if output_files:
            self.output_files=output_files
        else:
            self.output_files=[self.trace_file]

        self.profiling_args=profiling_args

    @property
    def global_metrics(self):
        """ Return a dictionnary with metrics that could be used outside this pofiler """
        return {}
        
    def get_profile_cmd(self,pid=None):
        """ Return profiling command """
        return ""

    def analyze(self):
        """ Standard analyze method """
        pass

    def report(self):
        """ Standard reporting method """
        pass
