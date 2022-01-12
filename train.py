# encoding: utf-8
"""
[Mender]
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2021.12.12

[Original]
Author: VincLee8188
GitHub: https://github.com/VincLee8188/GMAN-PyTorch
"""
import os
import time
import argparse
import torch

import torch.optim as optim
import torch.nn as nn

from model.utils_ import log_string, plot_train_val_loss
from model.utils_ import count_parameters, load_data

from model.model_ import GMAN
from model.train import train
from model.test import test

from src.utils import build_folder, saveJson

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--time_slot', type=int, default=5,
                        help='a time step is 5 mins')
    parser.add_argument('--num_his', type=int, default=5,
                        help='history steps')
    parser.add_argument('--num_pred', type=int, default=1,
                        help='prediction steps')

    parser.add_argument('--L', type=int, default=1,
                        help='number of STAtt Blocks')
    parser.add_argument('--K', type=int, default=8,
                        help='number of attention heads')
    parser.add_argument('--d', type=int, default=8,
                        help='dims of each head attention outputs')

    parser.add_argument('--train_ratio', type=float, default=0.7,
                        help='training set [default : 0.7]')
    parser.add_argument('--val_ratio', type=float, default=0.1,
                        help='validation set [default : 0.1]')
    parser.add_argument('--test_ratio', type=float, default=0.2,
                        help='testing set [default : 0.2]')

    parser.add_argument('--batch_size', type=int, default=24,
                        help='batch size')
    parser.add_argument('--max_epoch', type=int, default=50,
                        help='epoch to run')
    parser.add_argument('--patience', type=int, default=50,
                        help='patience for early stop')
    parser.add_argument('--learning_rate', type=float, default=0.001,
                        help='initial learning rate')
    parser.add_argument('--decay_epoch', type=int, default=10,
                        help='decay epoch')

    parser.add_argument('--traffic_file', default='./model/data/pems-bay.h5',
                        help='traffic file')
    parser.add_argument('--SE_file', default='./model/data/SE(PeMS).txt',
                        help='spatial embedding file')
    parser.add_argument('--model_file', default='./output/GMAN.pkl',
                        help='save the model to disk')
    parser.add_argument('--log_file', default='./output/log.txt',
                        help='log file')

    parser.add_argument('--output_folder', type=str, default='./output')
    parser.add_argument('--view_batch_freq', type=int, default=100)
    parser.add_argument('--device', default='gpu', 
                        help='cpu or cuda')

    # parser.add_argument('--unuse_id', default='',
    #                     help='unuse id')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = get_args()
    output_folder = os.path.dirname(args.log_file)
    args.device = 'cuda' if torch.cuda.is_available() and args.device in ['gpu', 'cuda'] else 'cpu'
    fig_folder = os.path.join(args.output_folder, 'figure')
    build_folder(args.output_folder)
    build_folder(fig_folder)
    
    T = 24 * 60 // args.time_slot  # Number of time steps in one day
    saveJson(args.__dict__, os.path.join(output_folder, 'configures.json'))

    log = open(args.log_file, 'w')
    log_string(log, str(args)[10: -1])
    log_string(log, f'main output folder{output_folder}')

    # load data >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    log_string(log, 'loading data...')
    (trainX, trainTE, trainY, valX, valTE, valY, testX, testTE,
    testY, SE, mean, std) = load_data(args)
    log_string(log, f'trainX: {trainX.shape}\t\t trainY: {trainY.shape}')
    log_string(log, f'valX:   {valX.shape}\t\tvalY:   {valY.shape}')
    log_string(log, f'testX:   {testX.shape}\t\ttestY:   {testY.shape}')
    log_string(log, f'mean:   {mean:.4f}\t\tstd:   {std:.4f}')
    log_string(log, 'data loaded!')
    del trainX, trainTE, valX, valTE, testX, testTE, mean, std
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # build model >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    log_string(log, 'compiling model...')

    model = GMAN(SE, args, bn_decay=0.1)
    # 要把 tensor 放到 cuda 才會使用，原本沒加
    if torch.cuda.is_available():
        model = model.to(args.device)
    
    loss_criterion = nn.MSELoss()

    optimizer = optim.Adam(model.parameters(), args.learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer,
                                        step_size=args.decay_epoch,
                                        gamma=0.9)
    parameters = count_parameters(model)
    log_string(log, 'trainable parameters: {:,}'.format(parameters))
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # train model >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    start = time.time()
    loss_train, loss_val = train(model, args, log, loss_criterion, optimizer, scheduler)
    saveJson({'train_loss': list(loss_train), 'val_loss': list(loss_val)}, os.path.join(output_folder, 'epoch_loss.json'))
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # test model >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    plot_train_val_loss(loss_train, loss_val, 
                os.path.join(fig_folder, 'train_val_loss.png'))
    trainPred, valPred, testPred, eval_dt = test(args, log)
    saveJson(eval_dt, os.path.join(output_folder, 'evaluation.json'))
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    end = time.time()
    log_string(log, 'total time: %.1fmin' % ((end - start) / 60))
    log.close()

    trainPred_ = trainPred.numpy().reshape(-1, trainY.shape[-1])
    trainY_ = trainY.numpy().reshape(-1, trainY.shape[-1])
    valPred_ = valPred.numpy().reshape(-1, valY.shape[-1])
    valY_ = valY.numpy().reshape(-1, valY.shape[-1])
    testPred_ = testPred.numpy().reshape(-1, testY.shape[-1])
    testY_ = testY.numpy().reshape(-1, testY.shape[-1])

    # Save training, validation and testing datas to disk
    l = [trainPred_, trainY_, valPred_, valY_, testPred_, testY_]
    name = ['trainPred', 'trainY', 'valPred', 'valY', 'testPred', 'testY']
    # for i, data in enumerate(l):
    #     np.savetxt(os.path.join(fig_folder, name[i] + '.txt'), data, fmt='%s')

    pred_dt = {k:v.tolist()  for k,v in list(zip(name, l))}
    saveJson(pred_dt, os.path.join(output_folder, 'prediction.json'))

    sample_result_text = 'valmae({:.4f})_testmae({:.4f})_time({:.1f})'.format(eval_dt['val_mae'], eval_dt['test_mae'], end - start)
    open(os.path.join(output_folder, sample_result_text), 'w').write('')