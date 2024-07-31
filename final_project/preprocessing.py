import os
from tqdm import tqdm
import pandas as pd
import numpy as np
import tensorflow as tf
from keras.utils import load_img, img_to_array
from PIL import Image
# ----------------------------------------
# 4:3 ratio
IMAGE_SIZE = (160, 120)
# 3:2 ratio
# IMAGE_SIZE = (180, 120)
# ----------------------------------------

def convert_to_greyscale_pil(image):
    “”"
    Convert a colored image to greyscale using PIL.
    Args:
        image (PIL.Image.Image): Input colored image.
    Returns:
        PIL.Image.Image: Greyscale image.
    “”"
    greyscale_image = image.convert(‘L’)
    return greyscale_image

def image_crop_and_resize(image_array, target_size):
    “”"
    Crop and resize an image (input as an array) to a target size.
    “”"
    # Calculate cropping dimensions to maintain the target aspect ratio
    h1, w1 = image_array.shape[0], image_array.shape[1]
    target_aspect = target_size[1] / target_size[0]
    aspect = w1 / h1

    if aspect > target_aspect:
        new_width = int(target_aspect * h1)
        new_height = h1
    else:
        new_width = w1
        new_height = int(w1 / target_aspect)

    # Calculate cropping box
    left = (w1 - new_width) // 2
    top = (h1 - new_height) // 2
    right = left + new_width
    bottom = top + new_height

    # Crop the image
    image_cropped = tf.image.crop_to_bounding_box(image_array, top, left, new_height, new_width)

    # Resize the cropped image
    image_resized = tf.image.resize(image_cropped, target_size)
    
    return image_resized

def preprocess_data_part1(labels_df, IMAGE_PATH, target_size = IMAGE_SIZE, greyscale=False):
    “”"
    Generate lists of images as numpy arrays and labels.
    Params:
    -------
    IMAGE_PATH (str): Path to directory with the images.
    labels_df (pd.DataFrame): Dataframe with labels and paths to images.
    Returns:
    --------
    X (np.ndarray): Array of keras img objects. Images of shape (N, target_height, target_width, 3)
                    If greyscale = True, then shape is (N, target_height, target_width, 1)
    y (np.ndarray): Labels of shape (N,)
    “”"
    images = []
    labels = []

    # Create lists of images and labels
    for idx, row in labels_df.iterrows():
        img_path = row[‘path’]
        label = row[‘label_encoded’]

        # Add label to y list
        labels.append(label)

        # Read image
        img = load_img(os.path.join(IMAGE_PATH, img_path))
        img_array = img_to_array(img)

        # if greyscale
        if greyscale:
            img_pil = Image.fromarray(img_array.astype(‘uint8’))
            img_pil = convert_to_greyscale_pil(img_pil)
            img_array = img_to_array(img_pil)
            img_array = img_array.reshape((img_array.shape[0], img_array.shape[1], 1))  # Add channel dimension
        
        # Crop and resize the image
        img_array = image_crop_and_resize(img_array, target_size=target_size)
        
        # Append to images list
        images.append(img_array)
    
    # Stack images and transform to array
    images = np.stack(images)
    labels = np.array(labels).flatten()
    
    return images, labels

def data_split_and_augment(images, labels, splits):
    “”" Split data into train, validation and test sets; apply augmentations
    Params:
    -------
    images  (np.ndarray): Images of shape (N, 224, 224, 3)
    labels (np.ndarray): Labels of shape (N,)
    splits (tuple): 3 values summing to 1 defining split of train, validation and test sets
    Returns:
    --------
    X_train (np.ndarray): Train images of shape (N_train, 224, 224, 3)
    y_train (np.ndarray): Train labels of shape (N_train,)
    X_val (np.ndarray): Val images of shape (N_val, 224, 224, 3)
    y_val (np.ndarray): Val labels of shape (N_val,)
    X_test (np.ndarray): Test images of shape (N_test, 224, 224, 3)
    y_test (np.ndarray): Test labels of shape (N_test,)
    “”"
    # NOTE: Each time you run this cell, you’ll re-shuffle the data. The ordering will be the same due to the random seed generator
    tf.random.set_seed(1234)
    np.random.seed(1234)
    
    # shuffle data
    idx = np.random.permutation(images.shape[0])
    images, labels = images[idx], labels[idx]
    
    # create data splits (training, val, and test sets)
    split_points = [int(splits[0] * len(images)), int((splits[0]+splits[1]) * len(images))]
    X_train, X_val, X_test = np.split(images, [split_points[0], split_points[1]])
    y_train, y_val, y_test = np.split(labels, [split_points[0], split_points[1]])
    
    # image augmentation (random flip) on training data
    X_train_augm = tf.image.random_flip_left_right(X_train)
    
    # concatenate original X_train and augmented X_train_augm data (will double the count of images)
    X_train = tf.concat([X_train, X_train_augm], axis=0)
    
    # concatenate y_train (note the label is preserved)
    # y_train = tf.concat([y_train, y_train],axis=0)
    y_train = np.concatenate([y_train, y_train], axis=0)
    
    # shuffle X_train and y_train, i.e., shuffle two tensors in the same order
    shuffle = tf.random.shuffle(tf.range(tf.shape(X_train)[0], dtype=tf.int32))
    X_train = np.array(tf.gather(X_train, shuffle)) # transform X back to numpy array instead of tensor
    y_train = np.array(tf.gather(y_train, shuffle)) # transform y back to numpy array instead of tensor
    
    # rescale training, val, and test images by dividing each pixel by 255.0
    X_train = X_train / 255.0
    X_val = X_val / 255.0
    X_test = X_test / 255.0
    
    return X_train, y_train, X_val, y_val, X_test, y_test

