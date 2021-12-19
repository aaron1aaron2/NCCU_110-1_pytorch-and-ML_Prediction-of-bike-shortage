python data_helper_SE.py \
    --file_path data/youbike_sort/spot_info.csv \
    --output_folder data/train_data/SE \
    --id_col sno \
    --group_col sarea \
    --group 士林區 \
    --use_group True\
    --longitude_col lng \
    --latitude_col lat \
    --adj_threshold 0.1