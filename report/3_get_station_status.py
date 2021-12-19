# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2021.12.13
"""
import os
from re
import pandas as pd
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 步驟一（替換sans-serif字型）
plt.rcParams['axes.unicode_minus'] = False  # 步驟二（解決座標軸負數的負號顯示問題）

output_folder = 'output'
plot_output_folder = 'output/plot'
map_output_folder = 'output/map'

spot = pd.read_csv('output/2_spot_info.csv')
tran_data = pd.read_csv('output/2_tran_data.csv')

tran_data['value_variation_ratio_abs'] = tran_data['value_variation_ratio'].abs()

# 站點名並過去
tran_dt = spot[['sno', 'sna']].set_index('sno').to_dict()['sna']
tran_data['sna'] = tran_data['sno'].apply(lambda x: tran_dt[x])

# 觀察
plt.clf()
tran_data[['inventory_ratio', 'value_variation_ratio_abs']].plot.hist(bins=20, alpha=0.8, colormap='Set3', density=True)
plt.xlabel('Ratio')
plt.ylabel('Probability')
plt.title('Histogram of Inventory ratio')
plt.grid(True)
# plt.show()
plt.savefig(os.path.join(plot_output_folder, '3_Histogram-of-inventory-and-value-variation-ratio.png'))

# 空車 =================================================
zero_count = tran_data[tran_data['inventory_ratio']==0].groupby(['sna'])['start_time'].count()
zero_count.sort_values(ascending=False, inplace=True)

# 空車的 bar 
plt.clf()
ax = zero_count.plot.barh(color='purple', alpha=0.5)
ax.invert_yaxis()
plt.tight_layout()
plt.legend().remove()
# plt.show()
plt.savefig(os.path.join(plot_output_folder, '3_Bar_zero_inventory_count.png'))

# 空車的
zero_count = zero_count.reset_index().set_index('sna').join(spot[['sna', 'coordinate']].set_index('sna'))
zero_count['center'] = zero_count.coordinate.str.split(',')
zero_count['center'] = zero_count.center.apply(lambda x: [float(x[0]),float(x[1])])

heat_data = [c + [v] for c, v in zero_count[['center', 'start_time']].values]

m = folium.Map(
        [25.0992835, 121.5196859],
        zoom_start=13 , 
        tiles='http://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga',
        attr='Google'
        )  #中心區域的確定
HeatMap(heat_data).add_to(m)
m.save(map_output_folder + '/3_zero_inventory_heat_map.html')

# 前幾時間點的變化 ==========================================
# 取出庫存為 0 的前兩個小時流量資訊
idx_ls = tran_data[tran_data['inventory_ratio']==0].index

idx_ls_pre_2h = [list(range(i-4, i)) for i in idx_ls]
idx_ls_pre_2h = [v for i in idx_ls_pre_2h for v in i]
idx_ls_pre_2h = list(set(idx_ls_pre_2h ))


tran_data_2h = tran_data.loc[idx_ls_pre_2h]
tran_data_2h = tran_data_2h[tran_data_2h['inventory_ratio']!=0]

plt.clf()
plt.close('all')
f, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 4))

# rectangular box plot
bplot1 = ax1.boxplot(tran_data_2h['value_variation_ratio'].values,
                     vert=True,  # vertical box alignment
                     patch_artist=True)  
ax1.set_title('Value variation ratio')

# notch shape box plot
bplot2 = ax2.boxplot(tran_data_2h['inventory_ratio'].astype(float).values,
                     notch=True,  # notch shape
                     vert=True,  # vertical box alignment
                     patch_artist=True)
ax2.set_title('Inventory ratio')
# plt.show()
plt.savefig(os.path.join(plot_output_folder, '3_2hour_box.png'))

# 散布圖
plt.close('all')
plt.clf()
ax = tran_data_2h.plot.scatter(color='g', x='inventory_ratio', y='value_variation_ratio', alpha=0.5)
ax.invert_yaxis()
plt.tight_layout()
# plt.legend().remove()
# plt.show()
plt.savefig(os.path.join(plot_output_folder, '3_2hour_scatter.png'))

# 輸出站點狀態 ======================================================================
tran_data.loc[tran_data['inventory_ratio']==0, 'status'] = '缺車'
tran_data.loc[(tran_data['inventory_ratio']<=0.4) & (tran_data['value_variation_ratio']<=0.1), 'status'] = '可能缺車'
tran_data.loc[tran_data['status'].isna(), 'status'] = '正常'


tran_data.to_csv(os.path.join(output_folder, '3_tran_data_status.csv'), index=False)