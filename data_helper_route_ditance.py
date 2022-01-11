# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2021.12
"""
import argparse
import json
import os
import pandas as pd
import numpy as np

from src.utils import build_folder
from src.path_planning_by_group import get_linear_distance, to_whole_Htable, optimize_distance
from sub_project.google_map_route_distance_crawler import crawler


def get_args():
    parser = argparse.ArgumentParser()

    # data
    parser.add_argument('--file_path', type=str, default='output/location_info_newid.csv')
    parser.add_argument('--output_folder', type=str, default='train data/SE')

    # crawler
    parser.add_argument('--vehicle_type', type=str, default='car', help="car,bus,bike,walk") # 建議設為1，爬蟲程式碼是一段時間前寫的還未維護多開 tor 的部分。
    parser.add_argument('--core', type=int, default=1, help="多進程數量") # 建議設為1，爬蟲程式碼是一段時間前寫的還未維護多開 tor 的部分。
    parser.add_argument('--tor_path', type=str, default='sub_project/path_planing/tor-win32-0.4.5.8/Tor/tor.exe', help="多進程數量") # 建議設為1，爬蟲程式碼是一段時間前寫的還未維護多開 tor 的部分。


    args = parser.parse_args()

    return args 


def main():
    args = get_args()
    build_folder(args.output_folder)
    print('='*50+'\n[args]\n' + str(args)[10 : -1])
    json.dump(args.__dict__, open(os.path.join(args.output_folder, 'configures.json'), encoding='utf8', mode='w'), indent=2)

    
    # 建立 edge list 和對應距離
    spot = pd.read_csv(args.file_path, usecols=['sno', 'sna', 'tot', 'sarea', 'lat', 'lng'], dtype=str)
    spot['coordinate'] = spot['lat'] + ',' + spot['lng']
    spot['sno'] = spot['sno'].astype(int)
    spot.to_csv(args.output_folder + '/spot_info.csv', index=None)

    distance_Table_helf = get_linear_distance(spot, coor_col='coordinate', id_col='sno', unit='km')
    distance_Table_helf.to_csv(args.output_folder + '/distance_table_half.csv', index=None)

    distance_Table_all = to_whole_Htable(spot.copy(), distance_Table_helf, coor_col='coordinate', id_col='sno')
    distance_Table_all.to_csv(args.output_folder + '/distance_table_all.csv', index=None)

    googlecrawler = crawler.crawler(
            input_data = os.path.join(args.output_folder, 'distance_table_half.csv'), 
            tor_path = args.tor_path, 
            tor_confs_path = os.path.join(args.output_folder, 'tor_config'), 
            core=args.core,
            vehicle_type=args.vehicle_type
            )

    googlecrawler.run()
    # 整理資料

    # 參數
    crawler_data_type = 'half'

    # 讀取與整理爬取資料
    assert crawler_data_type in ['all', 'half']

    crawler_result = pd.read_csv(os.path.join(args.output_folder, f'distance_table_{crawler_data_type}_result.csv'), dtype=str, header=None)
    crawler_result.columns = ['coordinate_pair', 'route', 'original_str', 'item_type', 'initial_value', 'url']


    crawler_result = pd.pivot_table(crawler_result, values='initial_value', index=['coordinate_pair', 'route'],
                        columns='item_type', aggfunc=np.min, fill_value=0)

    crawler_result['distance_google_value(km)'] = crawler_result['distance'].str.extract("(\d+.*\d+)").astype(float)
    crawler_result['distance_google_value(km)'] = crawler_result.apply(
        lambda x: x['distance_google_value(km)'] if x['distance'].find('公尺')==-1 else x['distance_google_value(km)']/1000, axis=1)

    hour = crawler_result['trip duration'].str.extract("(\d+) 小時").fillna(0).astype(int)[0].to_list()
    minute = crawler_result['trip duration'].str.extract("(\d+) 分").fillna(0).astype(int)[0].to_list()

    crawler_result['time_value(min)'] = list(map(lambda x: x[0]*60 + x[1] , zip(hour, minute)))

    hour = crawler_result['trip duration(Smooth)'].str.extract("(\d+) 小時").fillna(0).astype(int)[0].to_list()
    minute = crawler_result['trip duration(Smooth)'].str.extract("(\d+) 分").fillna(0).astype(int)[0].to_list()

    crawler_result['smooth_time_value(min)'] = list(map(lambda x: x[0]*60 + x[1] , zip(hour, minute)))

    crawler_result.to_csv(os.path.join(args.output_folder, 'crawler_result_multi-route.csv'))

    # 最順暢的路作為依據
    crawler_result.reset_index(inplace=True)

    crawler_result_select = crawler_result.loc[crawler_result.groupby(['coordinate_pair'])['smooth_time_value(min)'].idxmax().values]
    crawler_result_select.to_csv(os.path.join(args.output_folder, 'crawler_result_route.csv'), index=False)

    # 反轉雙向
    crawler_result_select[['start_coordinate', 'end_coordinate']] = crawler_result_select['coordinate_pair'].str.split("/",expand=True)
    distance_Table_all = pd.read_csv(os.path.join(args.output_folder, 'distance_table_all.csv'), dtype=str)

    crawler_result_expend = optimize_distance(
                crawler_result_select,
                distance_Table_all[['start_id', 'end_id', 'start_coordinate', 'end_coordinate', 'linear_distance']],
                start_coor='start_coordinate',
                end_coor='end_coordinate', 
                )
    crawler_result_expend.drop('coordinate_pair', axis=1, inplace=True)
    crawler_result_expend.fillna(0, inplace=True)

    df = pd.read_csv(os.path.join(args.output_folder, 'spot_list.csv'), usecols=['no', 'name'], dtype=str)
    df.columns = ['start_id','start_name']
    crawler_result_expend = crawler_result_expend.merge(df, how='left', on=['start_id'])
    df.columns = ['end_id','end_name']
    crawler_result_expend = crawler_result_expend.merge(df, how='left', on=['end_id'])

    order = [
        'start_id', 'end_id', 'start_name', 'end_name', 'start_coordinate',	'end_coordinate', 
        'route', 'linear_distance', 'distance', 'distance_google_value(km)', 
        'trip duration(Smooth)', 'smooth_time_value(min)', 'trip duration', 'time_value(min)', 
    ]
    crawler_result_expend[order].to_csv(os.path.join(args.output_folder, 'crawler_result_2PointDistance.csv'), index=False)

if __name__ == '__main__':
    main()    