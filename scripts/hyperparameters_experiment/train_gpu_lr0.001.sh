output_folder_root="./output/hyperparameters_experiment__gpu_lr0.001"
python train.py --time_slot 10 --num_his 5 --num_pred 1 --batch_size 24 \
        --max_epoch 100 --patience 100 --learning_rate 0.001 \
        --traffic_file data/train_data/data.h5 \
        --SE_file data/train_data/SE/basic/SE.txt \
        --model_file "$output_folder_root"/model.pkl \
        --log_file "$output_folder_root"/log.txt \
        --output_folder $output_folder_root \
        --device gpu

# .bat
set output_folder_root="./output/hyperparameters_experiment__gpu_lr0.001"
python train.py --time_slot 10 --num_his 5 --num_pred 1 --batch_size 24 ^
        --max_epoch 100 --patience 100 --learning_rate 0.001 ^
        --traffic_file data/train_data/data.h5 ^
        --SE_file data/train_data/SE/basic/SE.txt ^
        --model_file %output_folder_root%/model.pkl ^
        --log_file %output_folder_root%/log.txt ^
        --output_folder %output_folder_root% ^
        --device gpu