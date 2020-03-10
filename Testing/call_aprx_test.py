# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 15:47:50 2020

@author: DConly

Testing:
    Does APRX call lead to unregistered folder being called?
    Does using scratchFolder do this?

"""
import os
import shutil

import arcpy

aprx = r"\\arcserver-svr\D\PPA_v2_SVR\PPA2_GIS_SVR\PPA2_GIS_SVR.aprx"
# aprx = arcpy.GetParameterAsText(0)
img = r"\\arcserver-svr\D\PPA_v2_SVR\PPA2_GIS_SVR\Capture.JPG"

out_folder = arcpy.env.scratchFolder

output = os.path.join(out_folder, os.path.basename(img))
shutil.copyfile(img, output)

arcpy.SetParameterAsText(0, aprx)


