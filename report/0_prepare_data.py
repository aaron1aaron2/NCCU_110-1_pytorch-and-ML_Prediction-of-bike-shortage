# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  20211213
"""
import os
import pandas as pd
from src import path_planning_by_group
from src.utils import build_folder

pd.options.mode.chained_assignment = None  # default='warn'

data_path = 'data/youbike_sort/data.csv'
spot_path = 'data/youbike_sort/spot_info.csv'

output_folder = 'report/output'
build_folder(output_folder)
for path in [data_path, spot_path]:
    assert os.path.exists(path), '找不到整理完的 Youbike 資料，關於獲取 Youbike 資料請看 (scripts/get_youbike_data.sh)'

# 1. 建立 edge list 和對應距離
spot = pd.read_csv(spot_path, usecols=['sno', 'sna', 'tot', 'sarea', 'lat', 'lng'], dtype=str)
spot['coordinate'] = spot['lat'] + ',' + spot['lng']
spot['sno'] = spot['sno'].astype(int)
spot.to_csv(output_folder + '/0-1_spot_info.csv', index=None)

distance_Table_helf = path_planning_by_group.get_linear_distance(spot, coor_col='coordinate', id_col='sno', unit='km')
distance_Table_helf.to_csv(output_folder + '/0-1_distance_table_half.csv', index=None)

distance_Table_all = path_planning_by_group.to_whole_Htable(spot.copy(), distance_Table_helf, coor_col='coordinate', id_col='sno')
distance_Table_all.to_csv(output_folder + '/0-1_distance_table_all.csv', index=None)


# 2. 建立站點時間區間的存量變化表
data = pd.read_csv(data_path, dtype={'sno':int, 'sbi':int, 'bemp':int, 'act':int, 'date':str, 'time':str})
data['day'] = data['date'].str.extract(r'\d+\.\d+\.(\d+)').astype(int)
data['minute'] = data['time'].str[2:4]
data['datetime'] = data['date'] + ' ' +data['time'].str[:4]

def get_flow_tran(df):
    df = df.sort_values(['day', 'time']) # apply 不能用對 df 用 inplace 結果會有問題

    df = df[df['minute'].isin(['00','30'])]

    time_value = df[['datetime', 'sbi']].values

    time_value_df = pd.concat([
            pd.DataFrame(time_value[:-1], columns=['start_time', 'start_value']),
            pd.DataFrame(time_value[1:], columns=['end_time', 'end_value'])
        ], axis=1)
    time_value_df['value_variation'] = time_value_df['end_value'] - time_value_df['start_value']

    # time_value_df = time_value_df.drop(['start_value', 'end_value'], axis=1)

    return time_value_df

result = data.groupby('sno').apply(get_flow_tran)
result.reset_index(inplace=True)
result.drop('level_1', axis=1, inplace=True)

spot['sno'] = spot['sno'].astype(int)

# 加入總量
result = result.merge(spot[['tot', 'sno']], how='left')
result['inventory_ratio'] = (result['start_value']/result['tot'].astype(int)).map(lambda x: round(x, 3))
result['value_variation_ratio'] = (result['value_variation']/result['tot'].astype(int)).map(lambda x: round(x, 3))

result.to_csv(
    output_folder + '/0-2_data_tran.csv', index=None
)