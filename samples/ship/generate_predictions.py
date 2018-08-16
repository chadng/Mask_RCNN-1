import pandas
import math
import re
import datetime
import time
import numpy as np
import tensorflow as tf
import os
import sys
import skimage.io
import pandas as pd
# Root directory of the project
ROOT_DIR = os.path.abspath("../../")

# Import Mask RCNN
sys.path.append(ROOT_DIR)  # To find local version of the library
from mrcnn import utils
from mrcnn import visualize
from mrcnn.visualize import display_images
import mrcnn.model as modellib
from mrcnn.model import log

from samples.ship import ship

# Directory to save logs and trained model
MODEL_DIR = os.path.join(ROOT_DIR, "logs")

# Path to trained weights
SHIP_WEIGHTS_PATH = "./logs/ship20180815T0023/mask_rcnn_ship_0030.h5"

# Config
config = ship.ShipConfig()
SHIP_DIR = os.path.join(ROOT_DIR, "/samples/ship/datasets")

# Override the training configurations with a few
# changes for inferencing.
class InferenceConfig(config.__class__):
    # Run detection on one image at a time
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

# Create model object in inference mode.
config = InferenceConfig()
model = modellib.MaskRCNN(mode="inference", model_dir=MODEL_DIR, config=config)

# Instantiate dataset
dataset = ship.ShipDataset()

# Load weights
model.load_weights(os.path.join(ROOT_DIR, SHIP_WEIGHTS_PATH), by_name=True)

class_names = ['BG', 'ship']

# Run detection
# Load image ids (filenames) and run length encoded pixels
images_path = "datasets/test"
sample_sub_csv = "sample_submission.csv"
# images_path = "datasets/val"
# sample_sub_csv = "val_ship_segmentations.csv"
sample_submission_df = pd.read_csv(os.path.join(images_path,sample_sub_csv))
unique_image_ids = sample_submission_df.ImageId.unique()

out_pred_rows = []
for image_id in unique_image_ids:
    image_path = os.path.join(images_path, image_id)
    if os.path.isfile(image_path):
        tic = time.clock()
        image = skimage.io.imread(image_path)
        results = model.detect([image], verbose=1)
        r = results[0]
        print("Scores",r['scores'])

        re_encoded_to_rle_list = []
        for i in np.arange(np.array(r['masks']).shape[-1]):
            boolean_mask = r['masks'][:,:,i]
            re_encoded_to_rle = dataset.rle_encode(boolean_mask)
            re_encoded_to_rle_list.append(re_encoded_to_rle)

        if len(re_encoded_to_rle_list) == 0:
            out_pred_rows += [{'ImageId': image_id, 'EncodedPixels': ''}]
        else:
            for rle_mask in re_encoded_to_rle_list:
                out_pred_rows += [{'ImageId': image_id, 'EncodedPixels': rle_mask}]

        toc = time.clock()
        print("Prediction time: ",toc-tic)

print(out_pred_rows)

submission_df = pd.DataFrame(out_pred_rows)[['ImageId', 'EncodedPixels']]

filename = "{}{:%Y%m%dT%H%M}.csv".format("submission_", datetime.datetime.now())
submission_df.to_csv(filename, index=False)
print("Submission CSV Shape", submission_df.shape)

# print("ROIS",r['rois'])
# print("Masks",r['masks'])
# print("Masks Shape",np.array(r['masks']).shape)
# print("Class IDs",r['class_ids'])
# print("Scores",r['scores'])
