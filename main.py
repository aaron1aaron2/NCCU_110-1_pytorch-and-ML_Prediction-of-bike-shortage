# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  20211212
"""
import os
import argparse

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--data_folder', type=str, default = 'data/youbike_sort',
                        help = '每月人流資料')
    parser.add_argument('--populartime_path', type=str, default = 'data/popular_time.csv',
                        help = '熱門時段資料')
    parser.add_argument('--googletrend_path', type=str, default = 'data/googletrend.csv',
                        help = '搜尋資料位置')

    args = parser.parse_args()

    return args

def check_args(args):
    data_path = os.path.join(args.data_folder, 'data.csv')
    spot_path = os.path.join(args.data_folder, 'spot_info.csv')

    output_folder = 'output'
    for path in [args.data_path, args.spot_path]:
        assert os.path.exists(path), '找不到整理完的 Youbike 資料，關於獲取 Youbike 資料請看 (scripts/get_youbike_data.sh)'

def main():
    # 1_get_station_status
    output_folder = 'output'
    plot_output_folder = 'output/plot'
    map_output_folder = 'output/map'

    spot = pd.read_csv('output/2_spot_info.csv')
    tran_data = pd.read_csv('output/2_tran_data.csv')

    tran_data['value_variation_ratio_abs'] = tran_data['value_variation_ratio'].abs()

    tran_dt = spot[['sno', 'sna']].set_index('sno').to_dict()['sna']
    tran_data['sna'] = tran_data['sno'].apply(lambda x: tran_dt[x])

    tran_data.loc[tran_data['inventory_ratio']==0, 'status'] = '缺車'
    tran_data.loc[(tran_data['inventory_ratio']<=0.4) & (tran_data['value_variation_ratio']<=0.1), 'status'] = '可能缺車'
    tran_data.loc[tran_data['status'].isna(), 'status'] = '正常'


    tran_data.to_csv(os.path.join(output_folder, '3_tran_data_status.csv'), index=False)

    return