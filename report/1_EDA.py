# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2021.12.8
"""
import os
import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt

output_folder = 'output'
plot_output_folder = 'output/plot'

spot_info = pd.read_csv(os.path.join(output_folder, '0-1_spot_info.csv'))
dt_table_half = pd.read_csv(os.path.join(output_folder, '0-1_distance_table_half.csv'))

# 觀察站點距離分布
dt_table_half['linear_distance'].plot.hist(bins=30, colormap='Set3', alpha=0.8, density=True)
plt.xlabel('Direct distance(km)')
plt.ylabel('Probability')
plt.title('Histogram of distance between stations')
plt.grid(True)
# plt.show()
plt.savefig(os.path.join(plot_output_folder, '1_Histogram-of-distance-between-stations.png'))
plt.clf()

result_dt = {}
for i in spot_info['sno'].unique():
    result_dt[i] = {}
    for dt in [0.1, 0.3, 0.5, 0.8, 1, 2]:
        tmp = dt_table_half[(dt_table_half['start_id']==i) | (dt_table_half['end_id']==i)]
        spot_num = tmp[tmp['linear_distance']<=dt].shape[0]
        result_dt[i][dt] = spot_num

dt_level_spot_num = pd.DataFrame(result_dt).T

dt_level_spot_num.reset_index(inplace=True)
dt_level_spot_num.rename(columns={'index':'sno'}, inplace=True)

dt_level_spot_num.to_csv(output_folder + '/1_distance_level_spot_num(km).csv', index=None)

dt_level_spot_num.describe().\
    rename(columns={0.1:'100', 0.3:'300', 0.5:'500', 0.8:'800', 1:'1000', 2:'2000'}).\
    drop('count').drop('sno', axis=1).round(2).\
    to_csv(output_folder + '/1_distance_level_spot_num_describe(meter).csv')

for dt in [0.1, 0.3, 0.5, 0.8, 1, 2]:
    dt_level_spot_num[dt].plot.hist(bins=10, colormap='Set3', alpha=0.8)
    plt.xlabel('Stations number')
    plt.ylabel('Frequency')
    plt.title(f'Histogram of stations number within {dt*1000} meters')
    plt.grid(True)
    # plt.show()
    plt.savefig(os.path.join(plot_output_folder, f'1_Histogram-of-stations-num-{dt*1000}meters.png'))
    plt.clf()