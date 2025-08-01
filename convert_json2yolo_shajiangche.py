# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

import contextlib
import json
from collections import defaultdict

import cv2
import pandas as pd
from PIL import Image

from utils import *
import shutil


def convert_coco_json(image_dir="../coco/images/", json_dir="../coco/annotations/", 
                      use_segments=False, cls91to80=False):
    """Converts COCO JSON format to YOLO label format, with options for segments and class mapping."""
    folder_name = os.path.basename(image_dir)
    print(f"Processing folder: {folder_name}")
    save_dir = folder_name.split('_')[0]

    os.makedirs(save_dir, exist_ok=True)
    coco80 = coco91_to_coco80_class()

    # Import json
    for json_file in sorted(Path(json_dir).resolve().glob("*.json")):
        # print(json_file, json_file.stem)
        # fn = Path(save_dir) / "labels" / json_file.stem.replace("instances_", "")  # folder name
        image_fn = Path(save_dir) / "images"  # folder name
        fn = Path(save_dir) / "labels"  # folder name
        # print("fn: ",fn)
        # fn.mkdir()
        os.makedirs(image_fn, exist_ok=True)
        os.makedirs(fn, exist_ok=True)  # make directory if not exists
        with open(json_file) as f:
            data = json.load(f)

        image_file_name = json_file.stem+".jpg"
        image_path = os.path.join(image_dir, image_file_name)
        img_width, img_height = data['imageWidth'], data['imageHeight']
        # print("image_path, img_width, img_height: ", image_path, img_width, img_height)
        with Image.open(image_path) as img:
            img_width, img_height = img.size
        # print(f"Image dimensions: width={img_width}, height={img_height}")

        bboxes = []
        for shape in data['shapes']:
            label = shape['label']
            
            if 'group_id' not in shape:
                print(f"group_id not found in shape: {shape}, file: {json_file}, label: {label}")
                continue

            cls = int(shape['group_id'])
            cls -= 1

            x_coords = [point[0] for point in shape['points']]
            y_coords = [point[1] for point in shape['points']]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            # x_min, x_max = int(min(x_coords)), int(max(x_coords))
            # y_min, y_max = int(min(y_coords)), int(max(y_coords))

            box = np.array([x_min, y_min, x_max-x_min, y_max-y_min], dtype=np.float64)
            box[:2] += box[2:] / 2  # xy top-left corner to center
            box[[0, 2]] /= img_width  # normalize x
            box[[1, 3]] /= img_height  # normalize y
            
            if box[2] <= 0 or box[3] <= 0:  # if w <= 0 and h <= 0
                continue

            box = [cls] + box.tolist()
            # print(f"Box: {box}")
            if box not in bboxes:
                bboxes.append(box)

            # Copy image to output/images directory
            shutil.copy(image_path, image_fn / image_file_name)
            # Write
            with open((fn / image_file_name).with_suffix(".txt"), "w") as file:
                for i in range(len(bboxes)):
                    line = (*(bboxes[i]),)  # cls, box or segments
                    file.write(("%g " * len(line)).rstrip() % line + "\n")


def min_index(arr1, arr2):
    """
    Find a pair of indexes with the shortest distance.

    Args:
        arr1: (N, 2).
        arr2: (M, 2).

    Return:
        a pair of indexes(tuple).
    """
    dis = ((arr1[:, None, :] - arr2[None, :, :]) ** 2).sum(-1)
    return np.unravel_index(np.argmin(dis, axis=None), dis.shape)


def merge_multi_segment(segments):
    """
    Merge multi segments to one list. Find the coordinates with min distance between each segment, then connect these
    coordinates with one thin line to merge all segments into one.

    Args:
        segments(List(List)): original segmentations in coco's json file.
            like [segmentation1, segmentation2,...],
            each segmentation is a list of coordinates.
    """
    s = []
    segments = [np.array(i).reshape(-1, 2) for i in segments]
    idx_list = [[] for _ in range(len(segments))]

    # record the indexes with min distance between each segment
    for i in range(1, len(segments)):
        idx1, idx2 = min_index(segments[i - 1], segments[i])
        idx_list[i - 1].append(idx1)
        idx_list[i].append(idx2)

    # use two round to connect all the segments
    for k in range(2):
        # forward connection
        if k == 0:
            for i, idx in enumerate(idx_list):
                # middle segments have two indexes
                # reverse the index of middle segments
                if len(idx) == 2 and idx[0] > idx[1]:
                    idx = idx[::-1]
                    segments[i] = segments[i][::-1, :]

                segments[i] = np.roll(segments[i], -idx[0], axis=0)
                segments[i] = np.concatenate([segments[i], segments[i][:1]])
                # deal with the first segment and the last one
                if i in [0, len(idx_list) - 1]:
                    s.append(segments[i])
                else:
                    idx = [0, idx[1] - idx[0]]
                    s.append(segments[i][idx[0] : idx[1] + 1])

        else:
            for i in range(len(idx_list) - 1, -1, -1):
                if i not in [0, len(idx_list) - 1]:
                    idx = idx_list[i]
                    nidx = abs(idx[1] - idx[0])
                    s.append(segments[i][nidx:])
    return s


def delete_dsstore(path="../datasets"):
    """Deletes Apple .DS_Store files recursively from a specified directory."""
    from pathlib import Path

    files = list(Path(path).rglob(".DS_store"))
    print(files)
    for f in files:
        f.unlink()


if __name__ == "__main__":
    source = "COCO"

    if source == "COCO":

        convert_coco_json(
            "D:/jinyfeng/datas/shajiangche/train_images",
            "D:/jinyfeng/datas/shajiangche/train_labels",  # directory with *.json
            use_segments=False,
            cls91to80=False,
        )
        convert_coco_json(
            "D:/jinyfeng/datas/shajiangche/val_images",
            "D:/jinyfeng/datas/shajiangche/val_labels",  # directory with *.json
            use_segments=False,
            cls91to80=False,
        )

    # zip results
    # os.system('zip -r ../coco.zip ../coco')
