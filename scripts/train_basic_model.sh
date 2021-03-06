output_folder_root="./output/basic"
SEfile="./data/train_data/SE/basic/SE.txt"
python train.py --time_slot 10 --num_his 5 --num_pred 1 --batch_size 24 \
        --max_epoch 100 --patience 100 --learning_rate 0.01 \
        --traffic_file data/train_data/data.h5 \
        --SE_file "$SEfile" \
        --model_file "$output_folder_root"/model.pkl \
        --log_file "$output_folder_root"/log.txt \
        --output_folder $output_folder_root \
        --device gpu