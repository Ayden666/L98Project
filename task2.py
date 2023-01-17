import matplotlib.pyplot as plt
import os
import re
import shutil
import string
import pydot
import json
import tensorflow as tf
from collections import Counter
import pandas as pd
import numpy as np

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from tensorflow.keras import regularizers
from tensorflow.keras import layers
from tensorflow.keras import losses
from tensorflow.keras import preprocessing
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences




def main():
    train_data= pd.read_csv('train.csv')
    train_data.dropna(axis = 0, how ='any', inplace=True) 
    train_data['Num_words_text'] = train_data['text'].apply(lambda x : len(str(x).split())) 
    mask = train_data['Num_words_text'] > 2
    train_data = train_data[mask]

    # Drop classes with less than 5 members
    counts = train_data.groupby('classification')['classification'].transform(len)
    train_data = train_data[counts >= 5]

    num_groups = train_data.groupby('classification')['classification'].ngroups

    max_train_sentence_length  = train_data['Num_words_text'].max()

    num_words = 20000
    tokenizer = Tokenizer(num_words=num_words, oov_token="unk")
    tokenizer.fit_on_texts(train_data['text'].tolist())

    X_train, X_valid, y_train, y_valid = train_test_split(train_data['text'].tolist(),\
                                                      train_data['classification'].tolist(),\
                                                      test_size=0.1,\
                                                      stratify=train_data['classification'].tolist(),\
                                                      random_state=0)

    x_train = np.array(tokenizer.texts_to_sequences(X_train))
    x_valid = np.array(tokenizer.texts_to_sequences(X_valid))

    x_train = pad_sequences(x_train, padding='post', maxlen=40)
    x_valid = pad_sequences(x_valid, padding='post', maxlen=40)

    le = LabelEncoder()

    train_labels = le.fit_transform(y_train)
    train_labels = np.asarray( tf.keras.utils.to_categorical(train_labels))

    valid_labels = le.transform(y_valid)
    valid_labels = np.asarray( tf.keras.utils.to_categorical(valid_labels))
    list(le.classes_)

    train_ds = tf.data.Dataset.from_tensor_slices((x_train,train_labels))
    valid_ds = tf.data.Dataset.from_tensor_slices((x_valid,valid_labels))

    max_features =20000
    embedding_dim =64
    sequence_length = 40

    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Embedding(max_features +1, embedding_dim, input_length=sequence_length,\
                                        embeddings_regularizer=regularizers.l2(0.0005)))                                    

    model.add(tf.keras.layers.Conv1D(128,3, activation='relu',\
                                    kernel_regularizer=regularizers.l2(0.0005),\
                                    bias_regularizer=regularizers.l2(0.0005)))                               


    model.add(tf.keras.layers.GlobalMaxPooling1D())

    model.add(tf.keras.layers.Dropout(0.5))

    model.add(tf.keras.layers.Dense(num_groups, activation='sigmoid',\
                                    kernel_regularizer=regularizers.l2(0.001),\
                                    bias_regularizer=regularizers.l2(0.001),))
                                
    model.summary()
    model.compile(loss=tf.keras.losses.CategoricalCrossentropy(from_logits=True), optimizer='Nadam', metrics=["CategoricalAccuracy"])

    epochs = 100
    history = model.fit(train_ds.shuffle(2000).batch(128),
                        epochs=epochs,
                        validation_data=valid_ds.batch(128),
                        verbose=1)

    model.save('trained_model') 
    json_string = tokenizer.to_json()
    with open('tokenizer.json', 'w') as outfile:
        json.dump(json_string, outfile)

    predict_data= pd.read_csv('predict.csv')

    x_predict  = np.array(tokenizer.texts_to_sequences(predict_data['text'].tolist()) )
    x_predict = pad_sequences(x_predict, padding='post', maxlen=40)

    predictions = model.predict(x_predict)
    predict_results = predictions.argmax(axis=1)
    pred_classes = le.inverse_transform(predict_results)

    predict_data['pred_class'] = pred_classes
    predict_data.to_csv('pred_output.csv', index=False)


if __name__ == "__main__":
    main()