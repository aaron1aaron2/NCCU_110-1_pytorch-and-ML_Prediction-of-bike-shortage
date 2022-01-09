import torch
import time
import math
import numpy as np
from .utils_ import log_string, metric
from .utils_ import load_data

def test(args, log):
    (trainX, trainTE, trainY, valX, valTE, valY, testX, testTE,
     testY, SE, mean, std) = load_data(args)
    num_train, _, num_vertex = trainX.shape
    num_val = valX.shape[0]
    num_test = testX.shape[0]
    train_num_batch = math.ceil(num_train / args.batch_size)
    val_num_batch = math.ceil(num_val / args.batch_size)
    test_num_batch = math.ceil(num_test / args.batch_size)

    model = torch.load(args.model_file)

    # test model
    log_string(log, '**** testing model ****')
    log_string(log, 'loading model from %s' % args.model_file)
    model = torch.load(args.model_file)
    log_string(log, 'model restored!')
    log_string(log, 'evaluating...')

    with torch.no_grad():

        trainPred = []
        for batch_idx in range(train_num_batch):
            start_idx = batch_idx * args.batch_size
            end_idx = min(num_train, (batch_idx + 1) * args.batch_size)
            X = trainX[start_idx: end_idx]
            TE = trainTE[start_idx: end_idx]
            if torch.cuda.is_available():
                X, TE = X.to(args.device), TE.to(args.device)

            pred_batch = model(X, TE)
            trainPred.append(pred_batch.detach().cpu().clone())
            del X, TE, pred_batch
        # trainPred = trainPred.cpu()
        trainPred = torch.from_numpy(np.concatenate(trainPred, axis=0))
        trainPred = trainPred * std + mean

        valPred = []
        for batch_idx in range(val_num_batch):
            start_idx = batch_idx * args.batch_size
            end_idx = min(num_val, (batch_idx + 1) * args.batch_size)
            X = valX[start_idx: end_idx]
            TE = valTE[start_idx: end_idx]
            if torch.cuda.is_available():
                X, TE = X.to(args.device), TE.to(args.device)

            pred_batch = model(X, TE)
            valPred.append(pred_batch.detach().cpu().clone())
            del X, TE, pred_batch
        # valPred = valPred.cpu()
        valPred = torch.from_numpy(np.concatenate(valPred, axis=0))
        valPred = valPred * std + mean

        testPred = []
        start_test = time.time()
        for batch_idx in range(test_num_batch):
            start_idx = batch_idx * args.batch_size
            end_idx = min(num_test, (batch_idx + 1) * args.batch_size)
            X = testX[start_idx: end_idx]
            TE = testTE[start_idx: end_idx]
            if torch.cuda.is_available():
                X, TE = X.to(args.device), TE.to(args.device)

            pred_batch = model(X, TE)
            testPred.append(pred_batch.detach().cpu().clone())
            del X, TE, pred_batch
        testPred = torch.from_numpy(np.concatenate(testPred, axis=0))
        testPred = testPred* std + mean
    end_test = time.time()

    train_mae, train_rmse, train_mape = metric(trainPred, trainY)
    val_mae, val_rmse, val_mape = metric(valPred, valY)
    test_mae, test_rmse, test_mape = metric(testPred, testY)

    log_string(log, 'testing time: %.1fs' % (end_test - start_test))
    log_string(log, '                MAE\t\tRMSE\t\tMAPE')
    log_string(log, 'train            %.2f\t\t%.2f\t\t%.2f%%' %
               (train_mae, train_rmse, train_mape * 100))
    log_string(log, 'val              %.2f\t\t%.2f\t\t%.2f%%' %
               (val_mae, val_rmse, val_mape * 100))
    log_string(log, 'test             %.2f\t\t%.2f\t\t%.2f%%' %
               (test_mae, test_rmse, test_mape * 100))
    log_string(log, 'performance in each prediction step')
    eval_dt = {
        'train_mae': train_mae, 'train_rmse': train_rmse, 'train_mape': train_mape,
        'val_mae': val_mae, 'val_rmse': val_rmse, 'val_mape': val_mape,
        'test_mae': test_mae, 'test_rmse': test_rmse, 'test_mape': test_mape
    }

    eval_dt = {k:v.tolist() for k,v in eval_dt.items()}

    MAE, RMSE, MAPE = [], [], []
    for step in range(args.num_pred):
        mae, rmse, mape = metric(testPred[:, step], testY[:, step])
        MAE.append(mae)
        RMSE.append(rmse)
        MAPE.append(mape)
        log_string(log, 'step: %02d         %.2f\t\t%.2f\t\t%.2f%%' %
                   (step + 1, mae, rmse, mape * 100))

    average_mae = np.mean(MAE)
    average_rmse = np.mean(RMSE)
    average_mape = np.mean(MAPE)

    log_string(
        log, 'average:         %.2f\t\t%.2f\t\t%.2f%%' %
             (average_mae, average_rmse, average_mape * 100))

    return trainPred, valPred, testPred, eval_dt
