import os
import shutil
import pandas as pd
from tqdm import tqdm
from PIL import Image
import subprocess

from constants import IMAGES_FOLDER_PATH, LABELS_PATH_FULL, LABELS_PATH_CROPPED, LABEL_ENCODE_DICT

def remove_emotion_folder(dataset_folder_path, emotion, labels_csv_file):
    """Removes the folder for the specified emotion and its records from the CSV file.
    
    Args:
        dataset_folder_path (str): The path to the dataset folder.
        emotion (str): The name of the emotion folder to remove.
        labels_csv_file (str): The path to the CSV file containing the labels.

    Returns:
        None
    """
    emotion_folder = os.path.join(dataset_folder_path, emotion)

    if os.path.exists(emotion_folder):
        shutil.rmtree(emotion_folder)
        print(f"Removed [{emotion}] folder.")

    # Filter out rows with 'ahegao' in the 'emotion' column
    df = pd.read_csv(labels_csv_file)
    df = df[df['label'] != emotion]
    df.to_csv(labels_csv_file, index=False)

    print(f"Removed [{emotion}] records from the CSV file.")
    return None


def flatten_data_folder(dataset_folder_path):
    """
    Flattens the directory structure of a dataset folder by moving all image files to a single root folder.

    Args:
        dataset_folder_path (str): The path to the dataset folder.

    Returns:
        None
    """
    # Create a new folder to store the flattened images
    flattened_folder_path = os.path.join(dataset_folder_path)
    os.makedirs(flattened_folder_path, exist_ok=True)

    # Iterate through each emotion subfolder
    for emotion_folder in os.listdir(dataset_folder_path):
        emotion_folder_path = os.path.join(dataset_folder_path, emotion_folder)

        # Skip if the path is not a directory
        if not os.path.isdir(emotion_folder_path):
            continue

        # Iterate through each image file in the emotion subfolder
        for image_file in os.listdir(emotion_folder_path):
            image_file_path = os.path.join(emotion_folder_path, image_file)
            destination_path = os.path.join(flattened_folder_path, image_file)

            # Skip if this image has already been copied to the root destination folder
            if os.path.exists(destination_path):
                continue

            # Copy the image file to the root folder
            shutil.copy(image_file_path, destination_path)

        # Finally, remove the emotion folder
        if os.path.isdir(emotion_folder_path):
            shutil.rmtree(emotion_folder_path)
            print(f"Moved images from '{emotion_folder}' folder into {flattened_folder_path}.")
    return None

def get_image_dim(image_path):
    with Image.open(image_path) as img:
        return img.size # returns (width, height)


def add_pixel_dimensions(df):
    """ Adds columns for image pixel width and pixel height for each image
        in the labels dataframe.
    """
    # for error catching in case you run this twice
    if 'width' in df.columns and 'height' in df.columns:
        df = df.drop(columns=['width', 'height'])

    image_folder_path = os.path.join('data', 'dataset')
    widths = []
    heights = []

    # use tqdm to make a progress bar while it works through the df (without the timer part of the bar)
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        image_path = os.path.join(image_folder_path, row['path'])
        if os.path.isfile(image_path):
            with Image.open(image_path) as img:
                dims = img.size
                widths.append(dims[0])
                heights.append(dims[1])
        else:
            widths.append(None)
            heights.append(None)
            print(f"Warning: Image not found at {image_path}")
    df['width'] = widths
    df['height'] = heights
    print(" -> Finished adding image dimensions to the dataframes.")
    return df



def encode_label(df, encoder_dict):
    """ Returns df where label column is encoded. """
    df['label_encoded'] = df['label'].map(encoder_dict)
    return df


def clean_up_labels_file(file_path: str, label_dict):
    """ Loads the labels csv file, removes the 'Unnamed: 0' column if it exists, 
        removes the 'emotion' folder from the 'path' column, adds columns for image 
        pixel width and pixel height, encodes the 'label' column, and saves the 
        updated dataframe to the same csv file.
    """
    df = pd.read_csv(file_path)

    df['path'] = df['path'].apply(lambda x: x.split('/', 1)[1] if x.find('/') != -1 else x)
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])

    df = add_pixel_dimensions(df)
    df = encode_label(df, label_dict)
    df.to_csv(file_path, index=False)
    return None



def isolate_cropped_images(input_file_path: str, output_file_path: str):
    """ Loads the labels csv file, filters out the non-cropped images, creates a new 
        csv file with only the cropped images.
    """
    df = pd.read_csv(input_file_path)
    # filter to only include rows with 'cropped_emotion' in the 'path' column
    df = df[df['path'].str.contains('cropped_emotion')]
    df.to_csv(output_file_path, index=False)
    return None



def download_unzip_kaggle_data():
    """ 
    Downloads the dataset from Kaggle and unzips it.
    """
    try:
        os.makedirs('data', exist_ok=True)
        os.chdir('data')
        
        # Download dataset from Kaggle
        result = subprocess.run(['kaggle', 'datasets', 'download', '-d', 'sujaykapadnis/emotion-recognition-dataset'], check=True)
        
        # Check if the download was successful
        if result.returncode != 0:
            raise Exception("Failed to download dataset from Kaggle.")
        
        # Unzip the downloaded dataset
        if os.path.exists('emotion-recognition-dataset.zip'):
            subprocess.run(['unzip', 'emotion-recognition-dataset.zip'], check=True)
        else:
            raise FileNotFoundError("Downloaded zip file not found.")
        
        # Remove the zip file
        if os.path.exists('emotion-recognition-dataset.zip'):
            os.remove('emotion-recognition-dataset.zip')
        
        # Uncomment these lines if running in Colab
        # if os.path.exists('dataset'):
        #     os.rename('dataset', 'data/dataset')
        # if os.path.exists('data.csv'):
        #     os.rename('data.csv', 'data/data.csv')
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Ensure the working directory is reset
        os.chdir('..')



if __name__ == "__main__":
    download_unzip_kaggle_data()
    remove_emotion_folder(IMAGES_FOLDER_PATH, 'Ahegao', LABELS_PATH_FULL)
    # remove_emotion_folder(IMAGES_FOLDER_PATH, 'Neutral', LABELS_PATH_FULL)
    flatten_data_folder(IMAGES_FOLDER_PATH)
    clean_up_labels_file(LABELS_PATH_FULL, LABEL_ENCODE_DICT) # Note this step takes a while as it opens every image file to record its dimensions.
    isolate_cropped_images(LABELS_PATH_FULL, LABELS_PATH_CROPPED)
