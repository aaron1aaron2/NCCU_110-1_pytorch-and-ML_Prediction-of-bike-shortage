python train.py --time_slot 10 --num_his 5 --num_pred 1 --batch_size 24 \
        --max_epoch 50 --patience 50 --learning_rate 0.01 \
        --traffic_file data/train_data/data.h5 \
        --SE_file data/train_data/SE/basic/SE.txt \
        --model_file ./output/basic/model.pkl \
        --log_file ./output/basic/log.txt \
        --output_folder ./output/basic \
        --device gpu