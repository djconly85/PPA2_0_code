# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 16:51:12 2020

@author: dconly
"""
import os
import sys
import site
import imp

import arcpy

version = sys.version

module_to_find = 'xlwings'

try:
    conda_env =   os.environ['CONDA_PREFIX']
except:
    conda_env = 'No value found for CONDA_PREFIX--maybe no activated conda env?'


try:
    imp.find_module(module_to_find)
    imp_msg = '{} does exist!'.format(module_to_find)
except ImportError:
    imp_msg = "{} not found.".format(module_to_find)

def_dir = os.getcwd()

pkg_dir = site.getsitepackages()[1]

msg = "python version = {}\nConda Env = {}\nDefault dir = {}\nPackages dir = {}\nModule check result: {}" \
      .format(version, conda_env, def_dir, pkg_dir, imp_msg)

arcpy.SetParameterAsText(0, msg)
