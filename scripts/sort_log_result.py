# encoding: utf-8
"""
@author: yen-nan ho
@contact: aaron1aaron2@gmail.com
"""
# 整理各個實驗的結果
import os
import re
import json
import pandas as pd

def sort_result(logs_path, output_folder, re_format, folder_name_extract, BertSE_type=None):
    folder_name = [re.match(re_format, f)[0] for f in os.listdir(logs_path) if re.match(re_format, f) != None]


    result_df = pd.DataFrame() 
    for file in folder_name:
        all_dt = {"folder_name": file}
        folder = os.path.join(logs_path, file)
        if os.path.exists(os.path.join(folder, "epoch_losses.json")):
            config = json.load(open(os.path.join(folder, "configures.json"), "r"))
            epoch_losses = json.load(open(os.path.join(folder, "epoch_losses.json"), "r"))
            evaluation_prediction = json.load(open(os.path.join(folder, "evaluation_prediction.json"), "r"))
            evaluation_prediction = {k:v for k, v in evaluation_prediction.items() if (k.find("predicted")==-1 & k.find("target")==-1)}

            # 合併資料
            all_dt.update(config)
            all_dt.update(epoch_losses)
            all_dt.update(evaluation_prediction)

            # 將 list 資料傳換成用空格分隔的字串
            all_dt = {k:(str(v) if type(v)!=list else ' '.join([str(i) for i in v])) for k, v in all_dt.items()}

            result_df = result_df.append(pd.DataFrame(all_dt, index=[0]))
        else:
            print(f'{folder} pass !')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    result_df.to_csv(os.path.join(output_folder, 'result.csv'), index=False)

    # 對每個 target number 選擇 val 結果最好的筆，作為模型(SE、BertSE)

    df = result_df.copy()
    del result_df

    tmp = df['folder_name'].str.extract(folder_name_extract)
    tmp = tmp[[i for i in tmp.columns if i not in df.columns]] 
    df = pd.concat([tmp, df], axis=1)


    normal = [ 0,  1,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
             19, 20, 21, 23, 24, 25, 26, 29, 30, 32, 34, 35, 36, 37, 38, 39, 40,
             41, 43, 44, 45, 46, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
             60, 62, 63, 69, 70, 71, 72]

    transfor = [2, 3, 22, 27, 28, 31, 33, 42, 49, 61, 64, 65, 66, 67, 68]


    tmp = df['target_number'].astype(int).apply(lambda x: 'normal' if x in normal else 'transfor')
    tmp.name = 'is_tran'

    df = pd.concat([tmp, df], axis=1)

    df.sort_values('val_mae', inplace=True)

    df.to_csv(os.path.join(output_folder, 'result_all.csv'), index=False)

    gb = df.groupby(['SE_type', 'target_number'])

    # gb['val_mae'].min()
    result = gb.head(1)
    result.to_csv(os.path.join(output_folder, 'result_sort.csv'), index=False)

# 使用全站點
files = ['20210520_dtall_se', '20210520_dtall_bertse1', '20210520_dtall_bertse2', '20210520_dtall_bertse3']

for file in files:
    sort_result(logs_path=f"output/logs/{file}",
                output_folder=f"output/result/{file}",
                re_format=r"(\w+)?SE_P(\d+)_Q(\d+)_tn(\d+)", 
                folder_name_extract=r'(?P<SE_type>\w+)_P(?P<P>\d+)_Q(?P<Q>\d+)_tn(?P<target_number>\d+)'
                )

# 距離篩選
files = ['20210525_dt1500_se', '20210525_dt2000_se', '20210526_dt2500_se',
		 '20210523_dt1500_bertse1', '20210523_dt2000_bertse1', '20210526_dt2500_bertse1',
		 '20210523_dt1500_bertse2', '20210523_dt2000_bertse2', '20210528_dt2500_bertse2',
		 '20210523_dt1500_bertse3', '20210523_dt2000_bertse3', '20210528_dt2500_bertse3']

for file in files:
    sort_result(logs_path=f"output/logs/{file}",
                output_folder=f"output/result/{file}",
                re_format=r"(\w+)?SE_P(\d+)_Q(\d+)_tn(\d+)_dt(\d+)", 
                folder_name_extract=r'(?P<SE_type>\w+)_P(?P<P>\d+)_Q(?P<Q>\d+)_tn(?P<target_number>\d+)'
                )

# 路徑篩選
files = ['20210526_rt1_se', '20210526_rt3_se', '20210526_rt5_se',
		 '20210526_rt1_bertse1', '20210526_rt3_bertse1', '20210526_rt5_bertse1',
		 '20210528_rt1_bertse2', '20210528_rt3_bertse2', '20210528_rt5_bertse2',
		 '20210528_rt1_bertse3', '20210528_rt3_bertse3', '20210529_rt5_bertse3']

files = ['20210529_rt5_bertse3']

for file in files:
    sort_result(logs_path=f"output/logs/{file}",
                output_folder=f"output/result/{file}",
                re_format=r"(\w+)?SE_P(\d+)_Q(\d+)_tn(\d+)_rt(\d+)", 
                folder_name_extract=r'(?P<SE_type>\w+)_P(?P<P>\d+)_Q(?P<Q>\d+)_tn(?P<target_number>\d+)'
                )

# ==============================================================================
# 合併不同實驗結果
import pandas as pd 
import os
import re

output_folder='output/result'

re_format=r'\d+_(.+)_(.+)'

files = [i for i in os.listdir(output_folder) if re.match(re_format, i)!=None]

result_df = pd.DataFrame()
for file in files:
    re_match = re.match(re_format, file)
    filter_type, bertSE_type = re_match[1], re_match[2]
    df = pd.read_csv(os.path.join(output_folder, file, 'result_sort.csv'))
    df['filter_type'] = filter_type
    df['bertSE_type'] = bertSE_type

    head_cols = ['bertSE_type', 'filter_type']
    df = df[head_cols + [col for col in df.columns if col not in head_cols]]
    result_df = result_df.append(df)

cols_use =['bertSE_type', 'filter_type', 'is_tran', 'SE_type', 'target_number', 'P', 
           'epoch', 'train_mae', 'train_rmse', 'train_mape', 'val_mae',
           'val_rmse', 'val_mape', 'test_mae', 'test_rmse', 'test_mape']

result_df.to_csv(os.path.join(output_folder, 'result_all.csv'), index=False)

result_df[cols_use].to_excel(os.path.join(output_folder, 'result_all.xlsx'), index=False)

# ==============================================================================
# 針對不同欄位基準，取 val 最高的


def get_first_in_group(df, rank_col, group_cols):
    df.sort_values(rank_col, inplace=True)

    gb = df.groupby(group_cols)

    result = gb.head(1)
    result.sort_values(group_cols, inplace=True)

    return result

df = result_df[cols_use].copy()

df_SEtype = get_first_in_group(df,
				rank_col='val_mae',
				group_cols=['target_number', 'SE_type'])

df_SEtype.to_excel('output/result/result_SEtype.xlsx', index=False)

df_all = get_first_in_group(df,
				rank_col='val_mae',
				group_cols=['target_number'])
df_all.to_excel('output/result/result_total.xlsx', index=False)


df_bertSEtype = get_first_in_group(df,
				rank_col='val_mae',
				group_cols=['target_number', 'bertSE_type'])
df_bertSEtype.to_excel('output/result/result_bertSE_type.xlsx', index=False)


df_filtertype = get_first_in_group(df,
				rank_col='val_mae',
				group_cols=['target_number', 'filter_type'])
df_filtertype.to_excel('output/result/result_filtertype.xlsx', index=False)

df_Ft_BS_type = get_first_in_group(df,
				rank_col='val_mae',
				group_cols=['target_number', 'filter_type', 'bertSE_type'])
df_Ft_BS_type.to_excel('output/result/result_filter_bertSE_type.xlsx', index=False)

# ==============================================================================
# # (補) 抽取又萱跑的站點
# yu_sample = [63, 7, 1, 70, 30, 45, 44, 5, 3, 28, 31, 33, 49, 65, 66, 67, 68]

# df = pd.read_excel(os.path.join(output_folder, 'result_all.xlsx'))

# df[df.target_number.isin(yu_sample)].to_excel(os.path.join(output_folder, 'result_all_yushan.xlsx'), index=False)



