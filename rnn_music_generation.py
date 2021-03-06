# -*- coding: utf-8 -*-
"""RNN Music Generation

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ISDAcmvfhbmdjEppy9te0dlds_DLgshO
"""

! git clone https://github.com/aamini/introtodeeplearning_labs.git
# % cd introtodeeplearning_labs
! git pull
# % cd ..

import tensorflow as tf 
tf.enable_eager_execution()

import numpy as np
import os
import time
import functools

import introtodeeplearning_labs as util
!apt-get install abcmidi timidity > /dev/null 2>&1

#Downloading Datasets
path_to_file = tf.keras.utils.get_file('irish.abc', 'https://raw.githubusercontent.com/aamini/introtodeeplearning_labs/2019/lab1/data/irish.abc')

text = open(path_to_file).read()
# length of text is the number of characters in it
print ('Length of text: {} characters'.format(len(text)))

util.play_generated_song(text)

vocab=sorted(set(text))
print(len(vocab))
char2index={v:i  for i,v in enumerate(vocab)}
text_as_int=np.array(char2index[x] for x in text )

idx2char = np.array(vocab)
print(idx2char)

vocab

# Creating a mapping from unique characters to indices
char2idx = {u:i for i, u in enumerate(vocab)}
text_as_int = np.array([char2idx[c] for c in text])
print(text_as_int)
idx2char = np.array(vocab)

seq_length = 100
examples_per_epoch = len(text)//seq_length


char_dataset = tf.data.Dataset.from_tensor_slices(text_as_int)

sequences=char_dataset.batch(seq_length+1, drop_remainder=True )

def split_input_target(chunk):
    input_text = chunk[:-1]
    target_text = chunk[1:]
    return input_text, target_text

'''TODO: use the map method to apply your function to the list of sequences to generate the dataset!'''
dataset = sequences.map(split_input_target)
dataset

for input_example, target_example in dataset.take(1):
  
  for i, (input_idx, target_idx) in enumerate(zip(input_example[:5], target_example[:5])):
      print("Step {:4d}".format(i))
      print("  input: {} ({:s})".format(input_idx, repr(idx2char[input_idx])))
      print("  expected output: {} ({:s})".format(target_idx, repr(idx2char[target_idx])))

"""Create training batches
Great! Now we have our text split into sequences of manageable size. But before we actually feed this data into our model, we'll shuffle the data (for the purpose of stochastic gradient descent) and then pack it into batches which will be used during training.
"""

# Batch size 
BATCH_SIZE = 64
steps_per_epoch = examples_per_epoch//BATCH_SIZE

# Buffer size is similar to a queue size
# This defines a manageable data size to put into memory, where elements are shuffled
BUFFER_SIZE = 10000

dataset = dataset.shuffle(BUFFER_SIZE).batch(BATCH_SIZE, drop_remainder=True)

# Examine the dimensions of the dataset
dataset

"""Now we're ready to define and train a RNN model on our ABC music dataset, and then use that trained model to generate a new song. We'll train our RNN using batches of song snippets from our dataset, which we generated in the previous section.

The model is based off the LSTM architecture, where we use a state vector to maintain information about the temporal relationships between consecutive characters. The final output of the LSTM is then fed into a fully connected [`Dense`](https://www.tensorflow.org/api_docs/python/tf/keras/layers/Dense) layer where we'll output a softmax over each character in the vocabulary, and then sample from this distribution to predict the next character. 

As we introduced in the first portion of this lab, we'll be using the Keras API, specifically, [`tf.keras.Sequential`](https://www.tensorflow.org/api_docs/python/tf/keras/models/Sequential), to define the model. Three layers are used to define the model:

* [`tf.keras.layers.Embedding`](https://www.tensorflow.org/api_docs/python/tf/keras/layers/Embedding): This is the input layer, consisting of a trainable lookup table that maps the numbers of each character to a vector with `embedding_dim` dimensions.
* [`tf.keras.layers.LSTM`](https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM): Our LSTM network, with size `units=rnn_units`. 
* [`tf.keras.layers.Dense`](https://www.tensorflow.org/api_docs/python/tf/keras/layers/Dense): The output layer, with `vocab_size` outputs.


<img src="https://raw.githubusercontent.com/aamini/introtodeeplearning_labs/2019/lab1/img/lstm_unrolled-01-01.png" alt="Drawing"/>
"""

# Length of the vocabulary in chars
vocab_size = len(vocab)

# The embedding dimension 
embedding_dim = 256

# The number of RNN units
'''TODO: after running through the lab, try changing the number of units in the network to see how it affects performance'''
rnn_units = 1024

if tf.test.is_gpu_available():
  LSTM = tf.keras.layers.CuDNNLSTM
else:
  LSTM = functools.partial(
    tf.keras.layers.LSTM, recurrent_activation='sigmoid')

LSTM = functools.partial(LSTM, 
  return_sequences=True, 
  recurrent_initializer='glorot_uniform',
  stateful=True
)

def build_model(vocab_size, embedding_dim, rnn_units, batch_size):
  model = tf.keras.Sequential([
    tf.keras.layers.Embedding(vocab_size, embedding_dim, 
                              batch_input_shape=[batch_size, None]),
    LSTM(rnn_units), # TODO: Define the dimensionality of the RNN
    tf.keras.layers.Dense(vocab_size) # TODO: Define the dimensionality of the Dense layer
  ])

  return model

model = build_model(vocab_size,embedding_dim,rnn_units,BATCH_SIZE)

model.summary()

for input_example_batch, target_example_batch in dataset.take(1): 
  example_batch_predictions = model(input_example_batch)
  print(example_batch_predictions.shape, "# (batch_size, sequence_length, vocab_size)")
(example_batch_predictions[0].shape)

sampled_indices = tf.random.multinomial(example_batch_predictions[0], num_samples=1)
sampled_indices = tf.squeeze(sampled_indices,axis=-1).numpy()
print(sampled_indices)

print("Input: \n", repr("".join(idx2char[input_example_batch[0]])))
print()
print("Next Char Predictions: \n", repr("".join(idx2char[sampled_indices ])))

def compute_loss(labels, logits):
  return tf.keras.backend.sparse_categorical_crossentropy(labels, logits, from_logits=True)

'''TODO: compute the loss using the example batch and predictions from above'''
example_batch_loss  = compute_loss(target_example_batch,example_batch_predictions)
print("Prediction shape: ", example_batch_predictions.shape, " # (batch_size, sequence_length, vocab_size)") 
print("scalar_loss:      ", example_batch_loss.numpy().mean())

# Training step
EPOCHS = 5 
'''TODO: experiment with different optimizers'''
'''How does changing this affect the network's performance?'''
optimizer = tf.train.AdamOptimizer() # TODO
checkpoint_dir = './training_checkpoints'
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")

history = []
plotter = util.PeriodicPlotter(sec=1, xlabel='Iterations', ylabel='Loss')
for epoch in range(EPOCHS):
    start = time.time()

    # Initialize the hidden state at the start of every epoch; initially is None
    hidden = model.reset_states()
    
    # Enumerate the dataset for use in training
    custom_msg = util.custom_progress_text("Loss: %(loss)2.2f")
    bar = util.create_progress_bar(custom_msg)
    for inp, target in bar(dataset):
        # Use tf.GradientTape()
        with tf.GradientTape() as tape:
            '''TODO: feed the current input into the model and generate predictions'''
            predictions = model(inp)
            '''TODO: compute the loss!'''
            loss = compute_loss(target,predictions)
        
        # Now, compute the gradients and try to minimize
        '''TODO: complete the function call for gradient computation'''
        grads = tape.gradient(loss,model.trainable_variables) # TODO
        optimizer.apply_gradients(zip(grads, model.trainable_variables))
        
        # Update the progress bar!
        history.append(loss.numpy().mean())
        custom_msg.update_mapping(loss=history[-1])
        plotter.plot(history)
        
    # Update the model with the changed weights!
    model.save_weights(checkpoint_prefix.format(epoch=epoch))

model = build_model(vocab_size, embedding_dim, rnn_units, batch_size=1)

model.load_weights(tf.train.latest_checkpoint(checkpoint_dir))

model.build(tf.TensorShape([1, None]))

model.summary()

def musicgenerator(model,start_string,length=1000):
  input_eval = [char2idx[s] for s in start_string]
  input_eval = tf.expand_dims(input_eval, 0)
  mysong_first=[]
  model.reset_states()
  bar = util.create_progress_bar()
  for i in bar(range(length)):
    next_item=model(input_eval)
    next_item=tf.squeeze(next_item,0)
    predicted_id=tf.multinomial(next_item,num_samples=1)[-1,0].numpy()
    next_item=tf.expand_dims([predicted_id],0)
    mysong_first.append(idx2char[predicted_id])
  res=start_string+''.join(mysong_first)

def generate_text(model, start_string, generation_length=10000):
  input_eval = [char2idx[s] for s in start_string]
  input_eval = tf.expand_dims(input_eval, 0)
  text_generated = []
  model.reset_states()
  bar = util.create_progress_bar()
  for i in bar(range(generation_length)):
      predictions = model(input_eval)
      predictions = tf.squeeze(predictions, 0)
      predicted_id = tf.multinomial(predictions, num_samples=1)[-1,0].numpy()  
      input_eval = tf.expand_dims([predicted_id], 0)
      text_generated.append(idx2char[predicted_id]) 
  return (start_string + ''.join(text_generated))

res=generate_text(model,'X')
util.play_generated_song(res)

predicted_id = tf.multinomial(predictions, num_samples=1)[0,0].numpy()
predicted_id

