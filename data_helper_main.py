# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2021.12.19
"""
import os
import argparse
import pandas as pd

from src.utils import build_folder, saveJson

def get_args():
    parser = argparse.ArgumentParser()

    # data
    parser.add_argument('--file_path', type=str, default='data/youbike_sort/spot_info.csv')
    parser.add_argument('--output_folder', type=str, default='output/train_data/')
    parser.add_argument('--group_col', type=str, default='sarea', help='群組欄位(youbike 資料以區為單位分區域)')
    parser.add_argument('--group', type=str, default=None, help='使用的群組(需要指定 group_col)，格式: 士林區,文山區')
    parser.add_argument('--use_group', type=bool, default=False, help='是否要每個 group 分別去建立點之間的連結')

    # crawler
    parser.add_argument('--core', type=int, default=1, help="多進程數量") # 建議設為1，爬蟲程式碼是一段時間前寫的還未維護多開 tor 的部分。
    parser.add_argument('--output_folder', type=str, default='train data/SE')

    args = parser.parse_args()

    return args 

def main():
    args = get_args()
    print("="*20 + '\n' + str(args))
    build_folder(args.output_folder)

    saveJson(args.__dict__, os.path.join(args.output_folder, 'configures.json'))
    
    output_path = os.path.join(args.output_folder, 'data.h5')

    if os.path.exists(output_path):
        print("data.h5 is already build at ({})".format(output_path))
        exit()
    else:
        print("building data.h5 at ({})".format(output_path))

        if args.group != None:
            df = pd.read_csv(args.file_path, usecols=[args.id_col, args.coordinate_col, args.group_col], dtype=str)
            group_use_ls = args.group.split(',')
            df = df[df[args.group_col].isin(group_use_ls)]
        else:
            df = pd.read_csv(args.file_path, usecols=[args.id_col, args.coordinate_col], dtype=str)
            
    df_mrt = pd.read_csv(args.file_path, usecols=['id','總人次','datetime'])
    df_mrt.columns = ['datetime', 'value', 'id'] 
    df_mrt['datetime'] = pd.to_datetime(df_mrt['datetime'])
    df_pvt = df_mrt.pivot(index='datetime', columns='id', values='value')
    df_pvt.to_csv(os.path.join(input_folder, 'mrt_matrix_{}.csv'.format(y)))
    df_pvt.to_hdf(os.path.join(output_folder, 'mrt_matrix_{}.h5'.format(y)), key='data', mode='w')\

if __name__ == '__main__':
    main()