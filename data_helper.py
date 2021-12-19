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

    parser.add_argument('--file_path', type=str, default='data/youbike_sort/data.csv')
    parser.add_argument('--output_folder', type=str, default='data/train_data/')
    parser.add_argument('--id_col', type=str, default='sno') 
    parser.add_argument('--value_col', type=str, default='sbi')
    parser.add_argument('--date_col', type=str, default='date')
    parser.add_argument('--time_col', type=str, default='time')

    parser.add_argument('--group_col', type=str, default='sarea', help='群組欄位，配合 --group 參數使用，可以篩選要那些區的資料')
    parser.add_argument('--group', type=str, default=None, help='使用的群組(需要指定 group_col)，格式: XX區,XX區')

    parser.add_argument('--with_csv', dest='with_csv', action='store_true', help='順便輸出csv')
    parser.add_argument('--no-csv', dest='with_csv', action='store_false', help='不輸出csv')

    parser.set_defaults(with_csv=True)

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

        col_reads = [args.id_col, args.value_col, args.date_col, args.time_col]
        if args.group != None:
            col_reads.append(args.group_col)
            df = pd.read_csv(args.file_path, usecols=col_reads, dtype=str)
            group_use_ls = args.group.split(',')
            df = df[df[args.group_col].isin(group_use_ls)]
        else:
            df = pd.read_csv(args.file_path, usecols=col_reads, dtype=str)

    # 轉換成 datetime 格式
    df['datetime'] = df[args.date_col] + '.' + df[args.time_col]
    df['datetime'] = pd.to_datetime(df['datetime'], format=r'%Y.%m.%d.%H%M%S')  

    # 將表扭曲成 row(datetime), columns(id), value
    df_pvt = df.pivot(index='datetime', columns=args.id_col, values=args.value_col)
    df_pvt.to_hdf(os.path.join(args.output_folder, 'data.h5'), key='data', mode='w')
    if args.with_csv:
        df_pvt.to_csv(os.path.join(args.output_folder, 'data.csv'))
    
    print(f'Successful output data to ({output_path})')

if __name__ == '__main__':
    main()