# coding=utf-8
# Copyright 2024 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Graph Convolutional Network layer, as in Kipf&Welling with modifications.

Modifications include the skip-connection and changing the nonlinearity to SeLU.
"""
from typing import Tuple
import tensorflow.compat.v2 as tf



class GCN(tf.keras.layers.Layer):
    """Implementation of Graph Convolutional Network (GCN) layer without using node features."""

    def __init__(self, num_nodes, n_channels, activation='selu', skip_connection=True):
        """Initializes the layer with specified parameters."""
        super(GCN, self).__init__()
        self.num_nodes = num_nodes  # Now provided at initialization
        self.n_channels = int(n_channels)
        self.skip_connection = skip_connection
        if isinstance(activation, str):
            self.activation = tf.keras.layers.Activation(activation)
        elif isinstance(activation, tf.keras.layers.Activation):
            self.activation = activation
        elif activation is None:
            self.activation = tf.keras.layers.Lambda(lambda x: x)
        else:
            raise ValueError('GCN activation of unknown type')

    def build(self, input_shape):
        """Builds the layer with kernel initialized using provided num_nodes."""
        self.kernel = self.add_weight(
            name='kernel',
            shape=(self.num_nodes, self.n_channels),  # Now fixed at initialization
            initializer='glorot_uniform',
            trainable=True
        )
        self.bias = self.add_weight(
            name='bias',
            shape=(self.n_channels,),
            initializer='zeros',
            trainable=True
        )
        if self.skip_connection:
            self.skip_weight = self.add_weight(
                name='skip_weight',
                shape=(self.n_channels,),
                initializer='glorot_uniform',
                trainable=True
            )
        else:
            self.skip_weight = 0
        super().build(input_shape)

    def call(self, inputs):
        """Computes GCN representations using adjacency matrix only (no node features)."""
        _, norm_adjacency = inputs  # Ignore `features`
        
        assert isinstance(norm_adjacency, tf.SparseTensor)
        assert len(norm_adjacency.shape) == 2
        
        # Directly use the kernel (node embeddings) instead of `features`
        output = self.kernel + self.bias
        output = tf.sparse.sparse_dense_matmul(norm_adjacency, output)

        if self.skip_connection:
            output += self.skip_weight

        return self.activation(output)


class GCN_Original(tf.keras.layers.Layer):
  """Implementation of Graph Convolutional Network (GCN) layer.

  Attributes:
    n_channels: Output dimensionality of the layer.
    skip_connection: If True, node features are propagated without neighborhood
      aggregation.
    activation: Activation function to use for the final representations.
  """

  def __init__(self,
               n_channels,
               activation='selu',
               skip_connection = True):
    """Initializes the layer with specified parameters."""
    super(GCN, self).__init__()
    self.n_channels = n_channels
    self.skip_connection = skip_connection
    if isinstance(activation, str):
      self.activation = tf.keras.layers.Activation(activation)
    elif isinstance(tf.keras.layers.Activation):
      self.activation = activation
    elif activation is None:
      self.activation = tf.keras.layers.Lambda(lambda x: x)
    else:
      raise ValueError('GCN activation of unknown type')

  def build(self, input_shape):
    """Builds the Keras model according to the input shape."""
    self.n_features = input_shape[0][-1]
    self.kernel = self.add_weight(
        name='kernel',
        shape=(int(self.n_features), int(self.n_channels)),
        initializer='glorot_uniform',
        trainable=True
    )
    self.bias = self.add_weight(
        name='bias',
        shape=(int(self.n_channels),),
        initializer='zeros',
        trainable=True
    )
    if self.skip_connection:
        self.skip_weight = self.add_weight(
            name='skip_weight',
            shape=(int(self.n_channels),),
            initializer='glorot_uniform',
            trainable=True
        )
    else:
      self.skip_weight = 0
    super().build(input_shape)

  def call(self, inputs):
    """Computes GCN representations according to input features and input graph.

    Args:
      inputs: A tuple of Tensorflow tensors. First element is (n*d) node feature
        matrix and the second is normalized (n*n) sparse graph adjacency matrix.

    Returns:
      An (n*n_channels) node representation matrix.
    """
    features, norm_adjacency = inputs

    assert isinstance(features, tf.Tensor)
    assert isinstance(norm_adjacency, tf.SparseTensor)
    assert len(features.shape) == 2
    assert len(norm_adjacency.shape) == 2
    assert features.shape[0] == norm_adjacency.shape[0]

    '''output = tf.matmul(features, self.kernel)
    if self.skip_connection:
      output = output * self.skip_weight + tf.sparse.sparse_dense_matmul(
          norm_adjacency, output)
    else:
      output = tf.sparse.sparse_dense_matmul(norm_adjacency, output)
    output = output + self.bias'''
    
    output = tf.matmul(features, self.kernel) + self.bias
    output = tf.sparse.sparse_dense_matmul(norm_adjacency, output)
    if self.skip_connection:
        output += self.skip_weight

    return self.activation(output)
