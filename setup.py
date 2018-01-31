#!/usr/bin/env python
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

import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (3,4):
        sys.exit('Sorry, Python < 3.4 is not supported')

setup(name='lpprof',
      version='0.2',
      description='Lightweight Performance profiler using Linux perf_events.',
      author='EDF CCN HPC',
      author_email='dsp-cspito-ccn-hpc@edf.fr',
      license='GPLv3',
      platforms=['GNU/Linux'],
      url='https://github.com/edf-hpc/LPprofiler',
      scripts=['bin/lpprof','tests/tests_samples_profiler'],
      packages=['lpprofiler']
  )
