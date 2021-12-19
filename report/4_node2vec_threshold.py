# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  20211213

Notice: 需要先使用 data_helper_SE.py 產生 two_way_edge_table_LD.csv 檔。
refer: https://matplotlib.org/stable/gallery/statistics/boxplot_color.html
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def get_adj_value(df, threshold=0):
    '''The formula is `exponent (-1 * square (df['linear_distance']) / square (variance))`'''
    assert threshold>=0, '`threshold` must be greater than zero'
    Variation = np.var(df['linear_distance'].values)
    adj_ls = np.exp(-1*np.square(df['linear_distance'].values)/Variation)
    df['adj'] = list(map(lambda x: x if x >= threshold else 0, adj_ls))

    return df

if __name__ == '__main__':
    path = 'data/train_data/SE/basic/two_way_edge_table_LD.csv'
    df = pd.read_csv(path)

    df_adj = get_adj_value(df, threshold=0)
    info = df_adj['adj'].describe().round(5)

    # output -------------------
    # count    1296.00000
    # mean        0.23705
    # std         0.29931
    # min         0.00000
    # 25%         0.00373
    # 50%         0.07748
    # 75%         0.41191
    # max         1.00000
    # ---------------------------

    # df_adj.loc[df_adj['adj']>0.237050, 'adj'].plot(kind='box')
    # plt.show()
    # df_adj['adj'].plot(kind='box')
    # plt.show()
    # df_adj['linear_distance'].plot(kind='box', color='lightblue')
    # plt.show()

    # 資料整理 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    labels = ['zero', '25%', '50%', '75%', 'mean']
    adj_data_ls = []
    distance_data_ls = []
    for i in labels:
        if i == 'zero':
            adj_data_ls.append(df_adj['adj'].values)
            distance_data_ls.append(df_adj['linear_distance'].values)
        else:
            adj_data_ls.append(df_adj.loc[df_adj['adj']>info[i], 'adj'].values)
            distance_data_ls.append(df_adj.loc[df_adj['adj']>info[i], 'linear_distance'].values)
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # 畫箱型圖 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    plt.clf()
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10, 4))

    # rectangular box plot
    bplot1 = ax1.boxplot(adj_data_ls,
                        notch=True,  # notch shape
                        vert=True,  # vertical box alignment
                        patch_artist=True,  # fill with color
                        labels=labels)  # will be used to label x-ticks
    ax1.set_title('adj box plot')

    # notch shape box plot
    bplot2 = ax2.boxplot(distance_data_ls,
                        notch=True,  # notch shape
                        vert=True,  # vertical box alignment
                        patch_artist=True,  # fill with color
                        labels=labels)  # will be used to label x-ticks
    ax2.set_title('linear distance box plot')

    # fill with colors
    colors = ['pink', 'bisque', 'tan', 'orange', 'lightblue']
    for bplot in (bplot1, bplot2):
        for patch, color in zip(bplot['boxes'], colors):
            patch.set_facecolor(color)

    # adding horizontal grid lines
    for ax in [ax1, ax2]:
        ax.yaxis.grid(True)
        ax.set_xlabel('Samples less than the value')
    
    ax1.set_ylabel('adj values')
    ax1.set_xlabel('Samples more than the value')
    ax2.set_ylabel('linear distance values')
    ax2.set_xlabel('Samples less than the value')
    
    plt.savefig('report/output/4_assembly_boxplot.png')
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<