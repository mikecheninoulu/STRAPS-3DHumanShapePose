import os
import cv2

from predict.predict_3D import predict_3D


os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"  # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
predict_3D("/data/cvfs/as2562/datasets/toy_datasets/testing/cropped_frames", None,
           silhouettes_from='pointrend')