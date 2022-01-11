output_folder_root="./output/adj_threshold_experiment__th(0.34703)_75-percentile"

SEfile="./data/train_data/SE/test_adj/adj0.34703/SE.txt"
python train.py --time_slot 10 --num_his 5 --num_pred 1 --batch_size 24 \
        --max_epoch 50 --patience 100 --learning_rate 0.01 \
        --traffic_file data/train_data/data.h5 \
        --SE_file "$SEfile"\
        --model_file "$output_folder_root"/model.pkl \
        --log_file "$output_folder_root"/log.txt \
        --output_folder $output_folder_root \
        --device gpu