# make sure that web tool returns valid link for downloading output

import os
import arcpy
import pandas as pd

dummy_var = arcpy.GetParameterAsText(0) #string param

in_dict = {'a':[1,2,3],'b':[4,5,6]}
df = pd.DataFrame(in_dict)

out_csv = os.path.join(arcpy.env.scratchFolder, "data_out.csv")

df.to_csv(out_csv)

results = ("ok",out_csv)

result_csv = results[1]

arcpy.SetParameterAsText(1, result_csv)

"""
param0, string, input, optional
param1, file, output, derived
"""
