# Prediction of bike shortage and plan routes (Youbike in Taipei City)

## Quick Links
- [About](#about)
- [Quick Start](#quick-start)

## About

<p align="center"><img width="70%" src="img/Main_flow_chart.png" /></p>

## Quick Start
### Get youbike data
```
python sub_project/youbike_crawler/crawler.py --work_freq_in_min 10 --output_folder data/youbike
python sub_project/youbike_crawler/data_helper.py --crawler_output_folder data/youbike --output_folder data/youbike_sort
```
### prepare train data
```
data_helper.py --file_path data/youbike_sort/data.csv --output_folder 'data/train_data/' 
```
### prepare SE data
`on window`
```batch
python data_helper_SE.py ^
    --file_path data/youbike_sort/spot_info.csv ^
    --output_folder data/train_data/SE/basic ^
    --id_col sno ^
    --group_col sarea ^
    --group 文山區 ^
    --use_group True ^
    --longitude_col lng ^
    --latitude_col lat ^
    --adj_threshold 0.1
```
`on linux`
```shell
python data_helper_SE.py \
    --file_path data/youbike_sort/spot_info.csv \
    --output_folder data/train_data/SE \
    --id_col sno \
    --group_col sarea \
    --group 文山區 \
    --use_group True\
    --longitude_col lng \
    --latitude_col lat \
    --adj_threshold 0.1
```


## Model code source
https://github.com/VincLee8188/GMAN-PyTorch
## Citation
This version of implementation is only for learning purpose. For research, please refer to  and  cite from the following paper:
```
@inproceedings{ GMAN-AAAI2020,
  author = "Chuanpan Zheng and Xiaoliang Fan and Cheng Wang and Jianzhong Qi"
  title = "GMAN: A Graph Multi-Attention Network for Traffic Prediction",
  booktitle = "AAAI",
  pages = "1234--1241",
  year = "2020"
}
```