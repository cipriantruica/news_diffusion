import datetime
# import torch
import numpy as np
import os
import pickle
import random
import sys

import keras
from keras.utils import to_categorical
from keras.models import Sequential
from keras import layers
from keras.callbacks import ModelCheckpoint, Callback, EarlyStopping
from keras import losses
from keras import optimizers


from models.tweet import Tweet
from models.tweet_stats import TweetStats
from process_mabed_results import load_data
from settings.settings import load_environment
from vocabulary import Vocabulary
import time


NUMBER_OF_SOURCES = 7

VALIDATION_OFFSET = 10
TEST_OFFSET = 20
VALIDATION_OFFSET = 70
BATCH_SIZE = 5000
EPOCHS = 1500
TRAIN_OFFSET = 9


FIN = sys.argv[1]

es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=5)

def _tranform_y_data(y_data):
    new_y_data = np.zeros((y_data.shape[0], 3))
    for y in range(y_data.shape[0]):
        new_y_data[y] = np.array([1 if i == y_data[y][0] else 0 for i in range(3)])
    
    return new_y_data

def _transform_to_dataloader():
    # with open('experiment_%s.pickle' % experiment_no, 'rb') as experiment_file:
    with open(FIN, 'rb') as experiment_file:
        dataset = pickle.load(experiment_file)

    data = dataset['data']
    random.shuffle(data)

    train_limit = int(0.9 * len(data))

    # words + source + day of week

    validation_limit_per_class = 1400
    contors = ({'contor': 0}, {'contor': 0}, {'contor': 0})
    validation_data = []
    train_data = []
    
    for i in range(len(data)):
        if contors[0]['contor'] == 1400 and contors[1]['contor'] == 1400 and contors[2]['contor'] == 1400:
            train_data.append(data[i])
        else:
            data_class = data[i]['class']['favorites']
            if contors[data_class]['contor'] < 1400:
                validation_data.append(data[i])
                contors[data_class]['contor'] += 1
            else:
                train_data.append(data[i])
    print(len(train_data))
    train_data = train_data
    print(len(train_data))
    
    x_train = np.zeros((len(train_data), NO_FEATURES))
    y_train = np.zeros((len(train_data), 1))
    x_validation = np.zeros((len(validation_data), NO_FEATURES))
    y_validation = np.zeros((len(validation_data), 1))

    for i in range (len(train_data)):
        if NO_FEATURES == 308:
            x_train[i] = np.concatenate((train_data[i]['words'], train_data[i]['publisher_page'], np.array([1])))
        if NO_FEATURES == 300:
            x_train[i] = np.array(train_data[i]['words'])
        y_train[i] = np.array(train_data[i]['class']['favorites'])

    for i in range (len(validation_data)):
        if NO_FEATURES == 308:
            x_validation[i] = np.concatenate((validation_data[i]['words'], validation_data[i]['publisher_page'], np.array([1])))
        if NO_FEATURES == 300:
            x_train[i] = np.array(validation_data[i]['words'])
        # y_validation[i] = torch.tensor(np.array([data[data_index]['class']['favorites'], data[i]['class']['retweets']]))
        y_validation[i] = np.array([validation_data[i]['class']['favorites']])

    return [[(x_train, y_train), (x_validation, y_validation)],
            (None, None)]


class NBatchLogger(Callback):
    """
    A Logger that log average performance per `display` steps.
    """
    def __init__(self, display):
        self.step = 0
        self.display = display
        self.metric_cache = {}

    def on_batch_end(self, batch, logs={}):
        self.step += 1
        for k in self.params['metrics']:
            if k in logs:
                self.metric_cache[k] = self.metric_cache.get(k, 0) + logs[k]

        if self.step % self.display == 0:
            metrics_log = ''
            for (k, v) in self.metric_cache.items():
                val = v / self.display
                if abs(val) > 1e-3:
                    metrics_log += ' - %s: %.4f' % (k, val)
                else:
                    metrics_log += ' - %s: %.4e' % (k, val)
            print('step: {}/{} ... {}'.format(self.step,
                                          self.params['steps'],
                                          metrics_log))
            self.metric_cache.clear()


def _network1():    
    optimizer = optimizers.SGD(lr=0.5, momentum=0.8, clipvalue=0.5)

    model = Sequential()
    model.add(layers.Dense(units=150, activation='tanh', input_shape=(NO_FEATURES,)))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(units=100, activation='relu'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(units=3, activation='tanh'))
    model.add(layers.Softmax())
    model.compile(loss='mse', optimizer=optimizer, metrics=['accuracy'])

    [favorites_dataset, retweets_dl] = _transform_to_dataloader()

    x_train, y_train = favorites_dataset[0]
    x_validation, y_validation = favorites_dataset[1]

    # x_train = np.expand_dims(x_train, axis=1)
    y_train = _tranform_y_data(y_train)

    # x_validation = np.expand_dims(x_validation, axis=1)
    y_validation = _tranform_y_data(y_validation)
    
    x = model.fit(x_train, y_train, validation_split=0.3, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=1, shuffle=True, callbacks=[es])
    
    # print('Evaluate', model.evaluate(x_validation, y_validation))

def _network2():
    optimizer = optimizers.Adadelta(lr=2)

    model = Sequential()
    model.add(layers.Dense(units=150, activation='tanh', input_shape=(NO_FEATURES,)))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(units=100, activation='relu'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(units=3, activation='tanh'))
    model.add(layers.Softmax())
    model.compile(loss='mse', optimizer=optimizer, metrics=['accuracy'])

    [favorites_dataset, retweets_dl] = _transform_to_dataloader()

    x_train, y_train = favorites_dataset[0]
    x_validation, y_validation = favorites_dataset[1]

    # x_train = np.expand_dims(x_train, axis=1)
    y_train = _tranform_y_data(y_train)

    # x_validation = np.expand_dims(x_validation, axis=1)
    y_validation = _tranform_y_data(y_validation)

    x = model.fit(x_train, y_train, validation_split=0.3, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=1, shuffle=True, callbacks=[es])

    # print('Evaluate', model.evaluate(x_validation, y_validation))



def _network3():
    
    optimizer = optimizers.SGD(lr=0.5, momentum=0.8, clipvalue=0.5)

    model = Sequential()
    # output 44,6
    model.add(layers.Conv1D(filters=30, kernel_size=70, strides=2, activation='relu'))
    # output 11, 3
    if NO_FEATURES == 308:
        model.add(layers.MaxPool1D(120, 2))
    if NO_FEATURES == 300:
        model.add(layers.MaxPool1D(116, 2))
    model.add(layers.Dense(units=3, activation='softmax'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(units=3, activation='relu'))
    model.add(layers.Softmax())
    model.compile(loss=losses.categorical_crossentropy, optimizer=optimizer, metrics=['accuracy'])

    [favorites_dataset, retweets_dl] = _transform_to_dataloader()
    x_train, y_train = favorites_dataset[0]
    x_validation, y_validation = favorites_dataset[1]

    x_train = np.expand_dims(x_train, axis=2)
    y_train = np.expand_dims(to_categorical(y_train, num_classes=3), axis=1)
    
    x_validation = np.expand_dims(x_validation, axis=2)
    y_validation = np.expand_dims(to_categorical(y_validation, num_classes=3), axis=1)
    
    x = model.fit(x_train, y_train, validation_split=0.3, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=1, shuffle=True, callbacks=[es])
    
    # print('Evaluate', model.evaluate(x_validation, y_validation))
    

def _network4():
   
    optimizer = optimizers.Adadelta(lr=2)

    model = Sequential()
    # output 44,6
    model.add(layers.Conv1D(filters=30, kernel_size=70, strides=2, activation='relu'))
    # output 11, 3
    if NO_FEATURES == 308:
        model.add(layers.MaxPool1D(120, 2))
    if NO_FEATURES == 300:
        model.add(layers.MaxPool1D(116, 2))
    model.add(layers.Dense(units=3, activation='softmax'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(units=3, activation='relu'))
    model.add(layers.Softmax())
    model.compile(loss=losses.categorical_crossentropy, optimizer=optimizer, metrics=['accuracy'])

    [favorites_dataset, retweets_dl] = _transform_to_dataloader()
    x_train, y_train = favorites_dataset[0]
    x_validation, y_validation = favorites_dataset[1]

    x_train = np.expand_dims(x_train, axis=2)
    y_train = np.expand_dims(to_categorical(y_train, num_classes=3), axis=1)
    
    x_validation = np.expand_dims(x_validation, axis=2)
    y_validation = np.expand_dims(to_categorical(y_validation, num_classes=3), axis=1)
    
    x = model.fit(x_train, y_train, validation_split=0.3, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=1, shuffle=True, callbacks=[es])
    
    # print('Evaluate', model.evaluate(x_validation, y_validation))

if __name__ == '__main__':
    
    load_environment()

    NO_FEATURES = 300
    print(NO_FEATURES)
    
    start =time.time()
    _network1()
    end = time.time()
    elapsed = end - start
    print('MLP1', elapsed)

    start =time.time()
    _network2()
    end = time.time()
    elapsed = end - start
    print('MLP2', elapsed)

    start =time.time()
    _network3()
    end = time.time()
    elapsed = end - start
    print('CNN1', elapsed)

    start =time.time()
    _network4()
    end = time.time()
    elapsed = end - start
    print('CNN2', elapsed)

    NO_FEATURES = 308
    print(NO_FEATURES)

    start =time.time()
    _network1()
    end = time.time()
    elapsed = end - start
    print('MLP1', elapsed)

    start =time.time()
    _network2()
    end = time.time()
    elapsed = end - start
    print('MLP2', elapsed)

    start =time.time()
    _network3()
    end = time.time()
    elapsed = end - start
    print('CNN1', elapsed)

    start =time.time()
    _network4()
    end = time.time()
    elapsed = end - start
    print('CNN2', elapsed)
