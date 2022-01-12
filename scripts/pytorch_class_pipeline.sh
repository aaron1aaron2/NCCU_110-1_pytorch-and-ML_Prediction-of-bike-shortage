# youbike
python sub_project/youbike_crawler/crawler.py --work_freq_in_min 10 --output_folder data/youbike_raw
python sub_project/youbike_crawler/data_helper.py --crawler_output_folder data/youbike_raw --output_folder data/youbike_sort

# train_data
python data_helper.py --file_path data/youbike_sort/data.csv --output_folder data/train_data/ \
            --id_col sno --value_col sbi --group_col sarea --group 文山區 --with_csv

# SE-basic
python data_helper_SE.py \
    --file_path data/train_data/spot_info_id_table.csv \
    --output_folder data/train_data/SE/basic \
    --id_col new_id \
    --group_col sarea \
    --group 文山區 \
    --use_group True\
    --longitude_col lng \
    --latitude_col lat \
    --adj_threshold 0.1

# train model
python train.py --time_slot 10 --num_his 5 --num_pred 1 --batch_size 24 \
        --max_epoch 50 --patience 50 --learning_rate 0.01 \
        --traffic_file data/train_data/data.h5 \
        --SE_file data/train_data/SE/basic/SE.txt \
        --model_file ./output/basic/model.pkl \
        --log_file ./output/basic/log.txt \
        --output_folder ./output/basic \
        --device gpu