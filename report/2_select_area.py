# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  20211213
"""
import os
import functools
import pandas as pd
import numpy as np
import folium

from sub_project import path_planing

import seaborn as sns
# sns.set_theme(style="darkgrid")
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors
from pylab import *

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 步驟一（替換sans-serif字型）
plt.rcParams['axes.unicode_minus'] = False  # 步驟二（解決座標軸負數的負號顯示問題）

# from scipy import stats import spearmanr
from scipy.stats.mstats import spearmanr # 這不會有除以 0 問題

output_folder = 'output'
plot_output_folder = 'output/plot'
map_output_folder = 'output/map'
os.makedirs(plot_output_folder, exist_ok=True)
os.makedirs(map_output_folder, exist_ok=True)

spot_info = pd.read_csv(os.path.join(output_folder, '0-1_spot_info.csv'))
dt_table_half = pd.read_csv(os.path.join(output_folder, '0-1_distance_table_half.csv'))
tran_data = pd.read_csv(os.path.join(output_folder, '0-2_data_tran.csv'))

# 計算相關性

# 篩選 2公里以內(一般 15公里/小時 -> 20分鐘內為 5公里內 -> 行車距離換算直線距離大概 2公里內)
dt_table_half = dt_table_half[dt_table_half['linear_distance']<2]

def calculate_corr(id_pair, data):
    A = data[data['sno']==id_pair[0]]['value_variation'].values
    B = data[data['sno']==id_pair[1]]['value_variation'].values
    coor, p = spearmanr(A, B)

    return coor, p

# %time -> 13.6 秒
result = list(map(functools.partial(calculate_corr, data=tran_data), dt_table_half[['start_id', 'end_id']].values))

# 合併
dt_table_half = dt_table_half.join(pd.DataFrame(result, index=dt_table_half.index, columns=['spearman', 'p-value']))
dt_table_half.to_csv(output_folder + '/2_distance_table_2km_corr_pvalue.csv', index=None)

# 篩選 (spearman > 0.2 & p-value <0.05)
dt_table_half = dt_table_half[dt_table_half['spearman'] != 0]
dt_table_half['spearman_abs'] = dt_table_half['spearman'].abs()
dt_table_half = dt_table_half[(dt_table_half['spearman_abs']>0.2) & (dt_table_half['p-value']<0.05)]
dt_table_half.to_csv(output_folder + '/2_distance_table_2km_corr_pvalue(filter).csv', index=None)
# dt_table_half = pd.read_csv(output_folder + '/2_distance_table_2km_corr_pvalue(filter).csv')

# 視覺化
# plt.clf()
# sns.relplot(x="linear_distance", y="spearman_abs", data=dt_table_half)
# plt.tight_layout()
# plt.xlabel('Direct distance(km)')
# plt.ylabel('Absolute value of spearman')
# plt.savefig(os.path.join(plot_output_folder, '2_stations-relationship.png'))
# # plt.show()

dt_table_half['linear_distance_level'] = dt_table_half['linear_distance'].apply(lambda x: round(x*10)*100)
dt_table_half['linear_distance_level'] = dt_table_half['linear_distance_level'].apply(lambda x: '500' if x<=500 else (
    '500~1000' if 500<x<=1000 else (
    '1000~1500' if 1000<x<=1500 else '1500~2000'))
    )

plt.clf()
sns.catplot(x="linear_distance_level", y="spearman_abs",
            kind="violin", palette='Set3', split=True, data=dt_table_half)
plt.tight_layout()
plt.xlabel('Direct distance level(meters)')
plt.ylabel('Absolute value of spearman')
plt.savefig(os.path.join(plot_output_folder, '2_stations-relationship_violin.png'))
# plt.show()

# 畫地圖
map_data = path_planing.buildmap.data(output_folder + '/2_distance_table_2km_corr_pvalue(filter).csv', start_coor='start_coordinate', end_coor='end_coordinate')
map_data = map_data.merge(spot_info[['sno','sarea']].rename(columns={'sno':'start_id'}).astype(str), how='left')


cmap = cm.get_cmap('Set3', len(map_data['sarea'].unique()))    # PiYG

color_code_ls = []
for i in range(cmap.N):
    rgba = cmap(i)
    # rgb2hex accepts rgb or rgba
    color_code_ls.append(matplotlib.colors.rgb2hex(rgba))

color_code_dt = {area:color_code_ls[idx] for idx,area in enumerate(map_data['sarea'].unique())}
map_data['color'] = map_data['sarea'].apply(lambda x: color_code_dt[x])

# 製作圖例
plt.clf()
for area in color_code_dt:
    plt.plot(np.arange(10), np.random.rand(10) * 0, color_code_dt[area], label=area)
plt.legend(markerscale=2, framealpha=1)
plt.savefig(os.path.join(map_output_folder, 'stations_relat_map_legend.png'))
# plt.show()


m = folium.Map(
        [25.0992835, 121.5196859],
        zoom_start=13 , 
        tiles='http://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga',
        attr='Google'
        )  #中心區域的確定

for i in range(0,len(map_data)):
    location =[map_data['start_center'][i], map_data['end_center'][i]]

    label = '<br>spearman: {}'.format(map_data['spearman'][i]) +\
            '<br>p-value: {:.2f} 公里'.format(float(map_data['p-value'][i])) 

    folium.PolyLine( # polyline方法為將座標用線段形式連線起來
            location,    # 將座標點連線起來
            popup= folium.Popup(label, max_width=300, min_width=300), # 線的標記
            weight=7,    # 線的大小為3
            color=map_data['color'][i], # 線的顏色為橙色
            opacity=1,   # 線的透明度
            # fillColor='black',
            # fillOpacity=0.7
        ).add_to(m)

m.save(map_output_folder + '/2_stations_relat_map.html')


# 選擇包含士林區的站點
spot_info = pd.read_csv(os.path.join(output_folder, '0-1_spot_info.csv'))


# 取得邊界不屬於是林區有效的站點
dt_table_half = pd.read_csv(output_folder + '/2_distance_table_2km_corr_pvalue(filter).csv')
dt_table_half = dt_table_half.merge(spot_info[['sno','sarea']].rename(columns={'sno':'start_id'}), how='left')

other_id = dt_table_half[dt_table_half['sarea']=='士林區']['end_id'].unique()


# 篩選 & 輸出
id_select = list(set(other_id) | set(spot_info[spot_info['sarea']=='士林區']['sno'].unique()))

dt_table_half = pd.read_csv(os.path.join(output_folder, '0-1_distance_table_half.csv'))
dt_table_all = pd.read_csv(os.path.join(output_folder, '0-1_distance_table_all.csv'))
tran_data = pd.read_csv(os.path.join(output_folder, '0-2_data_tran.csv'))

spot_info[spot_info['sno'].isin(id_select)].to_csv(os.path.join(output_folder, '2_spot_info.csv'), index=None)
dt_table_half[dt_table_half['start_id'].isin(id_select) & dt_table_half['end_id'].isin(id_select)].\
    to_csv(os.path.join(output_folder, '2_distance_table_half.csv'), index=None)
dt_table_all[dt_table_all['start_id'].isin(id_select) & dt_table_all['end_id'].isin(id_select)].\
    to_csv(os.path.join(output_folder, '2_distance_table_all.csv'), index=None)

tran_data[tran_data['sno'].isin(id_select)].to_csv(os.path.join(output_folder, '2_tran_data.csv'), index=None)