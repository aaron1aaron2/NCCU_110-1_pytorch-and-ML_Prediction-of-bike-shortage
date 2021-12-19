import os
import re
import json
# encoding: utf-8
"""
@ author: yen-nan ho
@ contact: aaron1aaron2@gmail.com
@ date: 2021.12.2
"""
import tqdm
import argparse
import pandas as pd
import glob 

def get_args():
    parser = argparse.ArgumentParser('Youbike crawler:')

    parser.add_argument('--crawler_output_folder', default = 'output',
                        help = "輸出位置")
    parser.add_argument('--output_folder', default = 'output/result',
                        help = "輸出位置")

    args = parser.parse_args()

    return args

args = get_args()
output_folder = args.output_folder

os.makedirs(output_folder, exist_ok=True)
spot_feature = ['sno', 'sna', 'tot', 'sarea', 'lat', 'lng', 'ar', 'sareaen', 'snaen', 'aren']
dynamic_feature = ['sno', 'sbi', 'bemp', 'act', 'date', 'time']

if glob.glob(f'{args.crawler_output_folder}/*.json') != []:
    # 直接在 output
    files = glob.glob(f'{args.crawler_output_folder}/*.json')
elif glob.glob(f'{args.crawler_output_folder}/*/*.json') != []:
    # 有一層 date
    files = glob.glob(f'{args.crawler_output_folder}/*/*.json')

# 取站點基本資料
with open(files[0], mode='r', encoding='utf-8') as f:
    data = json.load(f)
df = pd.DataFrame(data).T
df[spot_feature].to_csv(os.path.join(output_folder, 'spot_info.csv'), index=False)

# 存取會變動資料
output_file = os.path.join(output_folder, 'data.csv')
for file in tqdm.tqdm(files):
    with open(file, mode='r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data).T
    
    pattern = r'(\d+\.\d+\.\d+)_(\d+)\.json'
    search_pat = re.search(pattern, file)
    df['date'] = search_pat[1]
    df['time'] = search_pat[2]

    if os.path.exists(output_file):
        df[dynamic_feature].to_csv(output_file, mode='a', header=False, index=False)
    else:
        df[dynamic_feature].to_csv(output_file, index=False)
