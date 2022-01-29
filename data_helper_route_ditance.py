# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2022.1.27
Last update: 2022.1.28
"""
import argparse
import json
import os
import pandas as pd
import numpy as np

from src.utils import build_folder
from src.path_planning_by_group import get_linear_distance, to_whole_Htable, optimize_distance
from sub_project.google_map_route_distance_crawler import crawler

from IPython import embed

def get_args():
    parser = argparse.ArgumentParser()

    # data
    parser.add_argument('--file_path', type=str, default='output/location_info_newid.csv')
    parser.add_argument('--output_folder', type=str, default='train data/SE')

    # crawler
    parser.add_argument('--vehicle_type', type=str, default='car', help="car,bus,bike,walk") # 建議設為1，爬蟲程式碼是一段時間前寫的還未維護多開 tor 的部分。

    # procces
    parser.add_argument('--select_route', type=str, default='distance', help="distance,trip duration") # 建議設為1，爬蟲程式碼是一段時間前寫的還未維護多開 tor 的部分。

    args = parser.parse_args()

    return args 


def main():
    args = get_args()
    build_folder(args.output_folder)
    print('='*50+'\n[args]\n' + str(args)[10 : -1])
    json.dump(args.__dict__, open(os.path.join(args.output_folder, 'configures.json'), encoding='utf8', mode='w'), indent=2)

    
    # 建立 edge list 和對應距離
    if os.path.exists(args.output_folder + '/distance_table_half.csv'):
        print(f'use cache file -> {args.output_folder}/distance_table_half.csv')
    else:
        print('Create edges for all sites')
        spot = pd.read_csv(args.file_path, usecols=['sno', 'sna', 'tot', 'sarea', 'lat', 'lng'], dtype=str)
        spot['coordinate'] = spot['lat'] + ',' + spot['lng']
        spot['sno'] = spot['sno'].astype(int)
        spot.to_csv(args.output_folder + '/spot_info.csv', index=None)

        distance_Table_helf = get_linear_distance(spot, coor_col='coordinate', id_col='sno', unit='km')
        distance_Table_helf.to_csv(args.output_folder + '/distance_table_half.csv', index=None)

        distance_Table_all = to_whole_Htable(spot.copy(), distance_Table_helf, coor_col='coordinate', id_col='sno')
        distance_Table_all.to_csv(args.output_folder + '/distance_table_all.csv', index=None)

  
    print('Crawling route(edge) info from google map')

    googlecrawler = crawler.crawler(
        input_data=os.path.join(args.output_folder, 'distance_table_half.csv'), 
        output_path=os.path.join(args.output_folder, 'crawler_back.csv'),
        vehicle_type=args.vehicle_type
        )
    googlecrawler.run()
    # 整理資料

    crawler_data_type = 'half'

    crawler_result = pd.read_csv(os.path.join(args.output_folder, f'crawler_back.csv'), dtype=str, header=None)
    crawler_result.columns = ['coordinate_pair', 'route', 'item_type', 'initial_value', 'original_str', 'url']

    # 轉換成每對經緯(coordinate_pair)下的每條路(route)，在不同類型的屬性中(item_type) 下抓取出來的值(initial_value)
    crawler_result = pd.pivot_table(crawler_result, values='initial_value', index=['coordinate_pair', 'route'],
                        columns='item_type', aggfunc=np.min, fill_value=0)

    # 統一將 ditance 轉換成公里為單位的值
    if 'distance' in crawler_result.columns:
        crawler_result['distance_value(km)'] = crawler_result['distance'].str.extract("(\d+.*\d+)").astype(float)
        crawler_result['distance_value(km)'] = crawler_result.apply(
            lambda x: x['distance_value(km)'] if x['distance'].find('公尺')==-1 else x['distance_value(km)']/1000, axis=1)
    
    # 統一將 trip duration 轉換成分鐘為單位的值
    if 'trip duration' in crawler_result.columns:
        hour = crawler_result['trip duration'].str.extract("(\d+) 小時").fillna(0).astype(int)[0].to_list()
        minute = crawler_result['trip duration'].str.extract("(\d+) 分").fillna(0).astype(int)[0].to_list()

        crawler_result['time_value(min)'] = list(map(lambda x: x[0]*60 + x[1] , zip(hour, minute)))
    
    # 統一將 trip duration(Smooth) 轉換成分鐘為單位的值 (開車才有)
    if 'trip duration(Smooth)' in crawler_result.columns:
        hour = crawler_result['trip duration(Smooth)'].str.extract("(\d+) 小時").fillna(0).astype(int)[0].to_list()
        minute = crawler_result['trip duration(Smooth)'].str.extract("(\d+) 分").fillna(0).astype(int)[0].to_list()

        crawler_result['smooth_time_value(min)'] = list(map(lambda x: x[0]*60 + x[1] , zip(hour, minute)))

    crawler_result.to_csv(os.path.join(args.output_folder, 'crawler_result_multi-route.csv'))

    # 選擇路線
    if args.select_route == 'distance':
        select_route = 'distance_value(km)'
    
    if args.select_route == 'trip duration':
        select_route = 'dtime_value(min)'
    crawler_result.reset_index(inplace=True)

    crawler_result_select = crawler_result.loc[crawler_result.groupby(['coordinate_pair'])[select_route].idxmax().values]
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

    df = pd.read_csv(os.path.join(args.output_folder, 'spot_info.csv'), usecols=['sno', 'sna'], dtype=str)
    df.columns = ['start_id','start_name']
    crawler_result_expend = crawler_result_expend.merge(df, how='left', on=['start_id'])
    df.columns = ['end_id','end_name']
    crawler_result_expend = crawler_result_expend.merge(df, how='left', on=['end_id'])

    embed()
    exit()
    order = [
        'start_id', 'end_id', 'start_name', 'end_name', 'start_coordinate',	'end_coordinate', 'route', 'linear_distance'
        ] + [i for i in crawler_result.columns if i!= 'coordinate_pair']
    crawler_result_expend[order].to_csv(os.path.join(args.output_folder, 'crawler_result_final.csv'), index=False)

if __name__ == '__main__':
    main()    