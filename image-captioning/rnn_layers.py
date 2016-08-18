import tensorflow as tf

def word_embedding_forward(captions_in, W_embed):
    """
    Inputs:
    - captions_in: input caption data (word index) for entire timeseries of shape (N, T).
    - W_embed: embedding matrix of shape (V, M).

    Returns:
    - out: word vector of shape (N, T, M).
    """
    out = tf.nn.embedding_lookup(W_embed, captions_in)
    return out

def rnn_step_forward(X, prev_h, Wx, Wh, b):
    """
    Inputs:
    - X: input data (word vector) for current time step of shape (N, M).
    - prev_h: previous hidden state of shape (N, H).
    - Wx: weight matrix for input-to-hidden of shape (M, H).
    - Wh: weight matrix for hidden-to-hidden of shape (H, H).
    - b: biases of shape (H,).

    Returns:
    - next_h: hidden states for current time step, of shape (N, H).
    """
    next_h = tf.nn.tanh(tf.matmul(X, Wx) + tf.matmul(prev_h, Wh) + b)
    return next_h

def rnn_forward(X, h0, Wx, Wh, b, param):
    """
    Inputs:
    - X: input data for the entire timeseries of shape (N, T, M).
    - h0: initial hidden state of shape (N, H).
    - Wx: weight matrix for input-to-hidden of shape (M, H).
    - Wh: weight matrix for hidden-to-hidden of shape (H, H).
    - b: biases of shape (H,).
    - rnn_param: dictionary with the following keys:
        - n_time_step: time step size

    Returns:
    - h: hidden states for the entire timeseries of shape (N, T, H).
    """
    T = param['n_time_step']
    prev_h = h0
    h_list = []

    for t in range(T):
        next_h = rnn_step_forward(X[:,t,:], prev_h, Wx, Wh, b)
        h_list.append(next_h)  # tensor flow doesn't provide item assignment such as h[:,t,:] = next_h
        prev_h = next_h

    h = tf.transpose(tf.pack(h_list), (1, 0, 2))
    return h

def temporal_affine_forward(X, W, b, param):
    """
    Inputs:
    - X: input data of shape (N, T, H)
    - W: weights of shape (H, V)
    - b: biases of shape (V,)
    - param: dictionary with the following keys:
        - batch_size: mini batch size 
        - n_time_step: time step size
        - dim_hidden: dimension of hidden state
        - vocab_size: vocabulary size

    Returns:
    - out: Output data of shape (N, T, V)
    """
    N = param['batch_size']
    T = param['n_time_step']
    H = param['dim_hidden']
    V = param['vocab_size']

    X = tf.reshape(X, [N*T,H])
    out = tf.matmul(X, W) + b
    return tf.reshape(out, [N,T,V])

def affine_forward(X, W, b):
    """
    Inputs:
    - X: input data of shape (N, F)
    - W: weights of shape (F, H)
    - b: biases of shape (H,)

    Returns:
    - out: output data of shape (N, H)
    """
    out = tf.matmul(X, W) + b
    return out

def temporal_softmax_loss(X, y, mask, param):
    """
    Inputs:
    - X: input scores of shape (N, T, V)
    - y: ground-truth indices of shape (N, T) where each element is in the range [0, V)
    - mask: boolean array of shape (N, T) where mask[i, t] tells whether or not
    the scores at x[i, t] should contribute to the loss.
    - param: dictionary with the following keys:
        - batch_size: mini batch size 
        - n_time_step: time step size
        - dim_hidden: dimension of hidden state
        - vocab_size: vocabulary size

    Returns:
    - loss: Scalar giving loss
    """
    N = param['batch_size']
    T = param['n_time_step']
    H = param['dim_hidden']
    V = param['vocab_size']

    X = tf.reshape(X, [N*T,V])
    y_onehot = tf.cast(tf.one_hot(y, V, on_value=1), tf.float32)
    y_onehot_flat = tf.reshape(y_onehot, [N*T,V])
    mask_flat = tf.reshape(mask, [N*T])
    loss = tf.nn.softmax_cross_entropy_with_logits(X, y_onehot_flat) * tf.cast(mask_flat, tf.float32)
    loss = tf.reduce_sum(loss)
    return loss