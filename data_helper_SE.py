# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2021.12.13
"""
import os
import argparse
import itertools
import pandas as pd
import numpy as np
from geopy.distance import geodesic

from src.utils import build_folder, saveJson, str2bool
from model.node2vec import generateSE 

pd.options.mode.chained_assignment = None  # default='warn'

def get_one_way_edge(df, group:str, coor_col:str, id_col:str):
    '''
    Group according to G, create a one-way-edge for all points in each group.

    point out
    ---
    There will be `(n-1)*n/2` lines(edge) at n points
    '''
    # 檢查輸入參數
    if group != None:
        cols = [group, coor_col, id_col]
    else:
        cols = [coor_col, id_col]

    for col in cols:
        assert col in df.columns, "'{}' not in dataframe! please check a column name.".format(col)
    
    df = df[cols]

    #產生配對
    if group != None:
        df_AB = df.groupby(df[group]).apply(lambda x:pd.DataFrame(list(itertools.combinations(x[id_col], 2))))
    else:
        df_AB = pd.DataFrame(list(itertools.combinations(df[id_col], 2)))

    df_AB.rename(columns={
                    0:'start_id',
                    1:'end_id'
                   }, 
                 inplace=True)

    #資料合併
    df.rename(columns={
                 '{}'.format(coor_col):'start_latlong',
                 '{}'.format(id_col):'start_id'
                }, 
              inplace=True)

    df_AB = pd.merge(df_AB, df, on=['start_id'], how='left')

    df.rename(columns={
                'start_latlong':'end_latlong',
                'start_id':'end_id'
                }, 
              inplace=True)

    df_AB = pd.merge(df_AB, df, on=['end_id'], how='left')
    
    return df_AB

def get_two_way_with_self(df, one_wey_table, coor_col:str, id_col:str):
    '''
    Flip two points and add the connection between the same points.
    Then we can get table, which can convert to  `distance matrix`.

    warn
    ---
    `start_id`, `end_id`, `start_latlong`, `end_latlong`, `linear_distance` must exist in the field.
    '''

    # 檢查參數
    for arg in [coor_col, id_col]:
        assert arg in df.columns, "[{}] not in dataframe input".format(arg)

    df = df[[id_col, coor_col]]

    #翻轉AB
    df.rename(columns={
        '{}'.format(id_col):'start_id',
        '{}'.format(coor_col):'start_latlong'}, inplace=True)


    df_end = df[['start_id','start_latlong']].rename(columns={
                                                        'start_id':'end_id',
                                                        'start_latlong':'end_latlong'
                                                        })
    df_self = pd.concat([df,df_end],sort=True,axis=1)
    
    #自己到自己補零
    df_self['linear_distance'] = np.zeros(shape=(len(df),1))

    one_wey_table_T = one_wey_table.rename(columns={
                                                'start_latlong':'end_latlong',
                                                'end_latlong':'start_latlong',
                                                'start_id':'end_id',
                                                'end_id':'start_id',
                                                'start_addr':'end_addr',
                                                'end_addr':'start_addr'
                                                })

    two_wey_table = pd.concat([one_wey_table, one_wey_table_T, df_self], sort=True)

    no = two_wey_table['start_id'].astype(str).str.extract(r'(?P<start_no>\d+)').astype(int)
    no2 = two_wey_table['end_id'].astype(str).str.extract(r'(?P<end_no>\d+)').astype(int)

    two_wey_table = pd.concat([two_wey_table, no, no2], axis=1)

    two_wey_table.sort_values(['start_no','end_no'], inplace=True) 


    return two_wey_table[['start_no', 'end_no', 'start_id', 'end_id', 'start_latlong', 'end_latlong', 'linear_distance']]

def get_linear_distance(df):
    '''
    Use two points of latitude and longitude to get the straight line distance.

    warn
    ---
    `start_latlong` and `end_latlong` must exist in the field. 

    Both `start_latlong` and `end_latlong` need to comply with the following format: "25.10514,121.5182"
    '''
    for col in ['start_latlong', 'end_latlong']:
        assert (col in df.columns)

    df['linear_distance'] = df.apply(lambda x:geodesic(x['start_latlong'].split(','),x['end_latlong'].split(',')).meters,axis=1)

    return df

def get_adj_value(df, threshold=0):
    '''The formula is `exponent (-1 * square (df['linear_distance']) / square (variance))`'''
    assert threshold>=0, '`threshold` must be greater than zero'
    Variation = np.var(df['linear_distance'].values)
    adj_ls = np.exp(-1*np.square(df['linear_distance'].values)/Variation)
    df['adj'] = list(map(lambda x: x if x >= threshold else 0, adj_ls))

    return df



def get_args():
    parser = argparse.ArgumentParser()

    # data
    parser.add_argument('--file_path', type=str, default='data/youbike_sort/spot_info.csv')
    parser.add_argument('--output_folder', type=str, default='output/train data/SE')
    parser.add_argument('--id_col', type=str, default='sno', help='點的編號欄位')
    parser.add_argument('--group_col', type=str, default='sarea', help='群組欄位(youbike 資料以區為單位分區域)')
    parser.add_argument('--group', type=str, default=None, help='使用的群組(需要指定 group_col)，格式: XX區,XX區')
    parser.add_argument('--use_group', type=str2bool, default=False, help='是否要每個 group 分別去建立點之間的連結')

    parser.add_argument('--coordinate_col', type=str, default=None, help='點的經緯度欄位(當需要計算距離時)，格式: 24.1580,121.6222')
    parser.add_argument('--longitude_col', type=str, default='lng', help='經度(當 --coordinate_col 未設定時會使用)')
    parser.add_argument('--latitude_col', type=str, default='lat', help='緯度(當 --coordinate_col 未設定時會使用)')

    # Adj martix
    parser.add_argument('--distance_method', type=str, default='linear distance')
    parser.add_argument('--adj_threshold', type=float, default=0.1, help='兩點關係程度的門檻值')

    # Node2vec
    parser.add_argument('--is_directed', type=bool, default=True)
    parser.add_argument('--p', type=float, default=2, help='控制走訪時，走回頭路的機率。p高可以減少走訪時回頭的機率。')
    parser.add_argument('--q', type=float, default=1, help='控制走訪時，走訪深度。q>1 頃向 BFS， q<1 頃向 DFS。')
    parser.add_argument('--num_walks', type=int, default=100, help='跑過每個節點的次數')
    parser.add_argument('--walk_length', type=int, default=80,  help='每個節點走訪的次數')

    # word2vec
    parser.add_argument('--dimensions', type=int, default=64, help='Word2Vec 的輸出向量維度，也是 SE 的維度')
    parser.add_argument('--window_size', type=int, default=10, help='Word2Vec 的 window size')
    parser.add_argument('--itertime', type=int, default=1000,  help='Word2Vec 的迭帶次數')

    args = parser.parse_args()

    return args 



if __name__ == "__main__":

    args = get_args()
    print("="*20 + '\n' + str(args))
    build_folder(args.output_folder)

    saveJson(args.__dict__, os.path.join(args.output_folder, 'configures.json'))

    Adj_file = os.path.join(args.output_folder, 'Adj.txt')
    SE_file = os.path.join(args.output_folder, 'SE.txt')

    # SE存在時就結束
    if os.path.exists(SE_file):
        print("SE_file is already build at ({})".format(SE_file))
        exit()

    # ADJ 資料
    if not os.path.exists(Adj_file):
        print("building Adj_file at ({})".format(Adj_file))

        # 準備資料
        if args.group != None:
            if args.coordinate_col != None:
                df = pd.read_csv(args.file_path, usecols=[args.id_col, args.coordinate_col, args.group_col], dtype=str)
            else:
                args.coordinate_col = 'coordinate'
                df = pd.read_csv(args.file_path, usecols=[args.id_col, args.longitude_col, args.latitude_col, args.group_col], dtype=str)
                df[args.coordinate_col] = df[args.latitude_col].str.strip() + ',' + df[args.longitude_col].str.strip()
                df.drop([args.longitude_col, args.latitude_col], inplace=True, axis=1)
                
            group_use_ls = args.group.split(',')
            df = df[df[args.group_col].isin(group_use_ls)]
        else:
            if args.coordinate_col != None:
                df = pd.read_csv(args.file_path, usecols=[args.id_col, args.coordinate_col], dtype=str)
            else:
                args.coordinate_col = 'coordinate'
                df = pd.read_csv(args.file_path, usecols=[args.id_col, args.longitude_col, args.latitude_col], dtype=str)
                df[args.coordinate_col] = df[args.latitude_col].str.strip() + ',' + df[args.longitude_col].str.strip()
                df.drop([args.longitude_col, args.latitude_col], inplace=True, axis=1)

        df = df[~df[args.coordinate_col].isna()]
        
        # 建立區域內連結
        print("number of nodes: {}".format(df.shape[0]))

        if args.use_group: 
            df_AB = get_one_way_edge(df, group=args.group_col, coor_col=args.coordinate_col, id_col=args.id_col)
        else:
            df_AB = get_one_way_edge(df, group=None, coor_col=args.coordinate_col, id_col=args.id_col)

        # 獲取各 edge 關係評估值
        print("shape of one way edge: {}".format(df_AB.shape))
        if args.distance_method ==  'linear distance':
            df_AB = get_linear_distance(df_AB) # 786 |308504 |2min 7s
        else:
            assert False, 'please set the parameter - `distance_method`'

        df_AB.to_csv(os.path.join(args.output_folder, 'one_way_edge_table_LD.csv'), index=False)

        # 建立雙向 edge 和自己到自己 (可直接轉成 disatnce martix)
        df_2W = get_two_way_with_self(df, df_AB, coor_col=args.coordinate_col, id_col=args.id_col)
        df_2W.to_csv(os.path.join(args.output_folder, 'two_way_edge_table_LD.csv'), index=False)

        # 計算 adj 值 (基於 GMAN 論文上的算法，越小關係越大)
        df_2W_adj = get_adj_value(df_2W, threshold=args.adj_threshold)
        df_2W_adj.to_csv(os.path.join(args.output_folder, 'two_way_edge_table_LD(adj).csv'), index=False)

        df_2W_adj[['start_no', 'end_no', 'adj']].to_csv(Adj_file, sep=' ', index=False, header=False)

    print("building SE_file at ({})".format(SE_file))

    # 訓練 Note2Vec 資料 (使用原始 GMAN 作者的程式碼 -> https://github.com/zhengchuanpan/GMAN/tree/master/PeMS/node2vec)
    train_node2vec = generateSE.SEDataHelper(
            is_directed=args.is_directed, p=args.p, q=args.q, 
            num_walks=args.num_walks, walk_length=args.walk_length,
            dimensions=args.dimensions, window_size=args.window_size,
            itertime=args.itertime,
            Adj_file=Adj_file,
            SE_file=SE_file
        )

    train_node2vec.run()