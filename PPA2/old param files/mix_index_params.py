# parameters for mix index


import pandas as pd


# input columns--MUST MATCH COLNAMES IN mix_idx_params_csv
col_parcelid = 'PARCELID'
col_hh = 'HH_hh'
col_emptot = 'EMPTOT'
col_empfood = 'EMPFOOD'
col_empret = 'EMPRET'
col_empsvc = 'EMPSVC'
col_k12_enr = 'ENR_K12'

# park acreage info
col_area_ac = 'GISAc'
col_lutype = 'LUTYPE'
lutype_parks = 'Park and/or Open Space'
col_parkac = 'PARK_AC'  # will be calc'd as GISAc if LUTYPE = park/open space LUTYPE
park_calc_dict = {'area_field': col_area_ac,
                  'lutype_field': col_lutype,
                  'park_lutype': lutype_parks,
                  'park_acres_field': col_parkac}

mix_idx_col = 'mix_index_1mi'

# by default, bal_ratio_per_hh = ratio of that land use factor per HH at the regional level, and represents "ideal" ratio
mix_calc_cols = ['lu_fac', 'bal_ratio_per_hh', 'weight']
mix_calc_vals = [['ENR_K12', 0.392079056, 0.2],
             ['EMPRET', 0.148253453, 0.4],
             ['EMPTOT', 1.085980023, 0.05],
             ['EMPSVC', 0.133409274, 0.1],
             ['EMPFOOD', 0.097047321, 0.2],
             ['PARK_AC', 0.269931832, 0.05]
             ]

params_df = pd.DataFrame(mix_calc_vals, columns = mix_calc_cols) \
    .set_index(mix_calc_cols[0])

if __name__ == '__main__':
    print(params_df)


