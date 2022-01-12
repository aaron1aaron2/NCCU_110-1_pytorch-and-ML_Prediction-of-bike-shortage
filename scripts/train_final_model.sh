output_folder_root="./output/final"
SEfile="./data/train_data/SE/test_adj/adj0.00124/SE.txt"
python train.py --time_slot 10 --num_his 2 --num_pred 1 --batch_size 5 \
        --max_epoch 50 --patience 100 --learning_rate 0.001 \
        --traffic_file data/train_data/data.h5 \
        --SE_file "$SEfile"\
        --model_file "$output_folder_root"/model.pkl \
        --log_file "$output_folder_root"/log.txt \
        --output_folder $output_folder_root \
        --device gpu