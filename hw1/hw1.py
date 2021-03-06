import sys
import math
import pandas as pd
import numpy as np

attrs = ['AMB', 'CH4', 'CO', 'NMHC', 'NO', 'NO2',
        'NOx', 'O3', 'PM10', 'PM2.5', 'RAINFALL', 'RH',
        'SO2', 'THC', 'WD_HR', 'WIND_DIR', 'WIND_SPEED', 'WS_HR']

attr_range = {}

for i, attr in enumerate(attrs):
    attr_range[attr] = list(range(9*i, 9*i+9))

def ReadTrainData(filename):
    raw_data = pd.read_csv(filename, encoding='big5').as_matrix()
    data = raw_data[:, 3:] # 12 months, 20 days per month, 18 features per day. shape: (4320 , 24)
    data[data == 'NR'] = 0.0
    data = data.astype('float')

    X, Y = [], []
    for i in range(0, data.shape[0], 18*20):
        # i: start of each month
        days = np.vsplit(data[i:i+18*20], 20) # shape: 20 * (18, 24)
        concat = np.concatenate(days, axis=1) # shape: (18, 480)
        for j in range(0, concat.shape[1]-9):
            X.append(concat[:, j:j+9].flatten())
            Y.append([concat[9, j+9]])

    return np.array(X), np.array(Y)

def ReadTestData(filename):
    raw_data = pd.read_csv(filename, header=None, encoding='big5').as_matrix()
    data = raw_data[:, 2:]
    data[data == 'NR'] = 0.0
    data = data.astype('float')

    obs = np.vsplit(data, data.shape[0]/18)
    X = []
    for i in obs:
        X.append(i.flatten())

    return np.array(X)

class Linear_Regression():
    def __init__(self):
        pass

    def _error(self, X, Y):
        return Y - self.predict(X)

    def _loss(self, X, Y):
        return np.sqrt(np.mean(self._error(X, Y) ** 2) + self.C * np.sum(self.W ** 2))

    def _init_parameters(self):
        self.B = 0.0
        self.W = np.ones((self.feature_dim, 1))

    def _scale(self, X, istrain=True):
        if istrain:
            self.min = np.min(X, axis=0)
            self.max = np.max(X, axis=0)
        return (X - self.min) / (self.max - self.min)

    def fit(self, _X, Y, valid, max_epoch=500000, lr=0.1, C=0.0):
        assert _X.shape[0] == Y.shape[0]
        N = _X.shape[0]
        self.feature_dim = feature_dim = _X.shape[1]
        self.C = C

        X = self._scale(_X)
        if valid is not None:
            X_valid, Y_valid = valid
            X_valid = self._scale(X_valid, istrain=False)

        self._init_parameters()

        B_lr = 0.0
        W_lr = np.zeros((feature_dim, 1))
        for epoch in range(1, max_epoch+1):
            error = self._error(X, Y)
            B_grad = -np.sum(error) * 1.0 / N
            W_grad = -np.dot(X.T, error) / N

            B_lr += B_grad ** 2
            W_lr += W_grad ** 2

            self.B = self.B - lr / np.sqrt(B_lr) * B_grad
            self.W = self.W * (1 - (lr / np.sqrt(W_lr)) * C) - lr / np.sqrt(W_lr) * W_grad

            if epoch % 1000 == 0:
                print('[Epoch {}]: loss: {}'.format(epoch, self._loss(X, Y)))
                if valid is not None:
                    print('valid loss: {}'.format(self._loss(X_valid, Y_valid)))

    def predict(self, X):
        _X = np.reshape(X, (-1, self.feature_dim))
        return np.dot(_X, self.W) + self.B
 
    def predict_test(self, X):
        _X = self._scale(X, istrain=False)
        _X = _X.reshape((-1, self.feature_dim))
        return np.dot(_X, self.W) + self.B

def main(args):
    X, Y = ReadTrainData(args[1])
    X_test = ReadTestData(args[2])

    select_attr = attrs
    select_attr = ['PM10', 'PM2.5', 'O3', 'CO', 'SO2', 'WIND_DIR', 'WIND_SPEED', 'WD_HR', 'WS_HR', 'RAINFALL']
    select_range = []
    for attr in select_attr:
        select_range += attr_range[attr]

    X = X[:, select_range]
    X_test = X_test[:, select_range]

    X = np.concatenate((X, X ** 2, X[:, 9:18] * X[:, 18:27]), axis=1)
    X_test = np.concatenate((X_test, X_test ** 2, X_test[:, 9:18] * X_test[:, 18:27]), axis=1)

    valid = None
    if len(args) >= 5:
        valid_num = int(args[4])
        order = np.random.permutation(X.shape[0])
        X, Y = X[order], Y[order]
        valid = X[-valid_num:], Y[-valid_num:]
        X, Y = X[:-valid_num], Y[:-valid_num]

    # remove July
    X, Y = np.concatenate((X[:2826, :], X[3297:, :])), np.concatenate((Y[:2826, :], Y[3297:, :]))
    model = Linear_Regression()
    model.fit(X, Y, valid=valid, max_epoch=35000, lr=0.5, C=0.0)

    predict = model.predict_test(X_test)
    with open(args[3], 'w') as f:
        print('id,value', file=f)
        for (i, p) in enumerate(predict) :
            print('id_{},{}'.format(i, p[0]), file=f)

if __name__ == '__main__':
    main(sys.argv)
