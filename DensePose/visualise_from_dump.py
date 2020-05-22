"""
Script that visualises and saves densepose results generated by apply_net.py in dump mode.
Only visualises for the largest person (largest bounding box) in the image.
Saves the I_image corresponding to each prediction as png images.
"""

import sys
import os
import pickle
import argparse
import numpy as np
import cv2

from densepose.structures import DensePoseResult
sys.path.append("/data/cvfs/as2562/detectron2/projects/DensePose/")
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def apply_colormap(image, vmin=None, vmax=None, cmap='viridis', cmap_seed=1):
    """
    Apply a matplotlib colormap to an image.

    This method will preserve the exact image size. `cmap` can be either a
    matplotlib colormap name, a discrete number, or a colormap instance. If it
    is a number, a discrete colormap will be generated based on the HSV
    colorspace. The permutation of colors is random and can be controlled with
    the `cmap_seed`. The state of the RNG is preserved.
    """
    image = image.astype("float64")  # Returns a copy.
    # Normalization.
    if vmin is not None:
        imin = float(vmin)
        image = np.clip(image, vmin, sys.float_info.max)
    else:
        imin = np.min(image)
    if vmax is not None:
        imax = float(vmax)
        image = np.clip(image, -sys.float_info.max, vmax)
    else:
        imax = np.max(image)
    image -= imin
    image /= (imax - imin)
    # Visualization.
    cmap_ = plt.get_cmap(cmap)
    vis = cmap_(image, bytes=True)
    return vis


def visualise_denspose_results(dump_file, out_folder):
    with open(dump_file, 'rb') as f_results:
        data = pickle.load(f_results)

    # Loop through frames
    for entry in data:
        frame_fname = entry['file_name']
        print(frame_fname)
        if out_folder == 'dataset':
            out_vis_path = frame_fname.replace('cropped_frames', 'densepose_vis')
            out_mask_path = frame_fname.replace('cropped_frames', 'densepose_masks')

            if not os.path.exists(os.path.dirname(out_vis_path)):
                os.makedirs(os.path.dirname(out_vis_path))
                os.makedirs(os.path.dirname(out_mask_path))
        elif out_folder == 'h36m':
            out_vis_path = frame_fname.replace('cropped_frames', 'densepose_vis')
            out_mask_path = frame_fname.replace('cropped_frames', 'densepose_masks')

            if not os.path.exists(os.path.dirname(out_vis_path)):
                os.makedirs(os.path.dirname(out_vis_path))
                os.makedirs(os.path.dirname(out_mask_path))
        else:
            raise NotImplementedError

        frame = cv2.imread(frame_fname)
        frame = frame.astype(np.float32)
        orig_h, orig_w = frame.shape[:2]

        # Choose the result instance (index) with largest bounding box that is also roughly
        # centred
        bboxes_xyxy = entry['pred_boxes_XYXY'].numpy()
        bboxes_area = (bboxes_xyxy[:, 2] - bboxes_xyxy[:, 0]) \
                      * (bboxes_xyxy[:, 3] - bboxes_xyxy[:, 1])
        # largest_centred_bbox_index = np.argmax(bboxes_area)
        sorted_bbox_indices = np.argsort(bboxes_area)[::-1]
        bbox_found = False
        i = 0
        print(bboxes_xyxy)
        print(bboxes_area)
        print(sorted_bbox_indices)
        while not bbox_found and i < sorted_bbox_indices.shape[0]:
            bbox_index = sorted_bbox_indices[i]
            bbox = bboxes_xyxy[bbox_index]
            bbox_centre = ((bbox[0]+bbox[2])/2.0, (bbox[1]+bbox[3])/2.0)
            if abs(bbox_centre[0] - orig_w/2.0) < 100 and abs(bbox_centre[1] - orig_h/2.0) < 100:
                largest_centred_bbox_index = bbox_index
                bbox_found = True
            i += 1

        # If can't find bbox sufficiently close to centre, just use biggest mask as prediction
        if not bbox_found:
            largest_centred_bbox_index = sorted_bbox_indices[0]

        result_encoded = entry['pred_densepose'].results[largest_centred_bbox_index]
        iuv_arr = DensePoseResult.decode_png_data(*result_encoded)

        # Round bbox to int
        largest_bbox = bboxes_xyxy[largest_centred_bbox_index]
        w1 = largest_bbox[0]
        w2 = largest_bbox[0] + iuv_arr.shape[2]
        h1 = largest_bbox[1]
        h2 = largest_bbox[1] + iuv_arr.shape[1]

        I_image = np.zeros((orig_h, orig_w))
        I_image[int(h1):int(h2), int(w1):int(w2)] = iuv_arr[0, :, :]
        # U_image = np.zeros((orig_h, orig_w))
        # U_image[int(h1):int(h2), int(w1):int(w2)] = iuv_arr[1, :, :]
        # V_image = np.zeros((orig_h, orig_w))
        # V_image[int(h1):int(h2), int(w1):int(w2)] = iuv_arr[2, :, :]

        # Save visualisation and I image (i.e. segmentation mask)
        vis_I_image = apply_colormap(I_image, vmin=0, vmax=24)
        vis_I_image = vis_I_image[:, :, :3].astype(np.float32)
        vis_I_image[I_image == 0, :] = np.zeros(3, dtype=np.float32)
        overlay = cv2.addWeighted(frame,
                                  0.6,
                                  vis_I_image,
                                  0.4,
                                  gamma=0)
        cv2.imwrite(out_vis_path, overlay)
        cv2.imwrite(out_mask_path, I_image)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dump_file', type=str)
    parser.add_argument('--out_folder', type=str)
    args = parser.parse_args()

    visualise_denspose_results(args.dump_file, args.out_folder)