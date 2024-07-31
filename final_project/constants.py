import os

# folder paths
IMAGES_FOLDER_PATH = os.path.join('data', 'dataset')
LABELS_PATH_FULL = os.path.join('data', 'data.csv')
LABELS_PATH_CROPPED = os.path.join('data', 'data_cropped.csv')


LABEL_ENCODE_DICT = {'Happy': 0, 'Sad': 1, 'Angry': 2, 'Surprise': 3, 'Neutral': 4}
LABEL_DECODE_DICT = {v: k for k, v in LABEL_ENCODE_DICT.items()}