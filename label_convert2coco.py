import os
import json
import shutil
from pycocotools import mask
import numpy as np

# 定义所有文件夹路径
# folder_paths = [
#     '/Users/jinyfeng/projects/ai-construction/20250426',
#     '/Users/jinyfeng/projects/ai-construction/20250430',
#     '/Users/jinyfeng/projects/ai-construction/20250504',
#     '/Users/jinyfeng/projects/ai-construction/20250507',
#     '/Users/jinyfeng/projects/ai-construction/20250508',
#     '/Users/jinyfeng/projects/ai-construction/20250509',
#     '/Users/jinyfeng/projects/ai-construction/20250510',
#     '/Users/jinyfeng/projects/ai-construction/20250511',
#     '/Users/jinyfeng/projects/ai-construction/20250512',
#     '/Users/jinyfeng/projects/ai-construction/20250513',
#     '/Users/jinyfeng/projects/ai-construction/20250514',
#     '/Users/jinyfeng/projects/ai-construction/20250515',
#     '/Users/jinyfeng/projects/ai-construction/20250516',
#     '/Users/jinyfeng/projects/ai-construction/20250517',
#     '/Users/jinyfeng/projects/ai-construction/20250518',
#     '/Users/jinyfeng/projects/ai-construction/20250519',
#     '/Users/jinyfeng/projects/ai-construction/20250520',
#     '/Users/jinyfeng/projects/ai-construction/20250521',
#     '/Users/jinyfeng/projects/ai-construction/20250522',
#     '/Users/jinyfeng/projects/ai-construction/20250523',
#     '/Users/jinyfeng/projects/ai-construction/20250524',
#     '/Users/jinyfeng/projects/ai-construction/20250525',
#     '/Users/jinyfeng/projects/ai-construction/20250526',
#     '/Users/jinyfeng/projects/ai-construction/20250527',
#     '/Users/jinyfeng/projects/ai-construction/20250528',
#     '/Users/jinyfeng/projects/ai-construction/20250529',
#     '/Users/jinyfeng/projects/ai-construction/20250530',
#     '/Users/jinyfeng/projects/ai-construction/20250602',
#     '/Users/jinyfeng/projects/ai-construction/20250604',
#     '/Users/jinyfeng/projects/ai-construction/20250605',
#     '/Users/jinyfeng/projects/ai-construction/20250606',
#     '/Users/jinyfeng/projects/ai-construction/20250609',
#     '/Users/jinyfeng/projects/ai-construction/20250610',
#     '/Users/jinyfeng/projects/ai-construction/20250611',
#     '/Users/jinyfeng/projects/ai-construction/20250612',
#     '/Users/jinyfeng/projects/ai-construction/20250613',
#     '/Users/jinyfeng/projects/ai-construction/20250614',
#     '/Users/jinyfeng/projects/ai-construction/20250616',
#     '/Users/jinyfeng/projects/ai-construction/20250617',
#     '/Users/jinyfeng/projects/ai-construction/20250618',
# ]

folder_paths = [
    '/Users/jinyfeng/projects/ai-construction/val',
]

# data_type = 'train'
data_type = 'val'

# 创建一个名为 "施工物料训练数据" 的文件夹
images_folder = '/Users/jinyfeng/projects/ai-construction/wuliao'+f'_{data_type}_images'
labels_folder = '/Users/jinyfeng/projects/ai-construction/wuliao'+f'_{data_type}_labels'
if not os.path.exists(images_folder):
    os.makedirs(images_folder, exist_ok=True)
if not os.path.exists(labels_folder):
    os.makedirs(labels_folder, exist_ok=True)

coco_images = []
coco_annotations = []
coco_categories = []
category_set = set()
annotation_id = 0

middle_four_dict = dict()
# 遍历每个文件夹路径
image_idx = 0
last_middle_four = None
for folder_path in folder_paths:
    print(f"Processing folder: {folder_path}")
    # 获取文件夹名称

    folder_name = os.path.basename(folder_path)
    if data_type == 'train':
        middle_four = folder_name[2:6]

        if middle_four not in middle_four_dict:
            middle_four_dict[middle_four] = 1
            image_idx = 1
        else:
            middle_four_dict[middle_four] += 1
            image_idx = middle_four_dict[middle_four]
    # 遍历文件夹中的所有 JSON 文件
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            # new_jpg_name = f"{folder_name}_{file_name.replace('.json', '.jpg')}"
            jpg_name = f"{file_name.replace('.json', '.jpg')}"
            jpg_file_path = os.path.join(folder_path, jpg_name)
            new_jpg_name = f"{folder_name}_{jpg_name}"
            new_jpg_path = os.path.join(images_folder, new_jpg_name)
            shutil.copy(jpg_file_path, new_jpg_path)

            # 打开并读取 JSON 文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data_type == 'val':
                middle_four = jpg_name[2:6]
                
                if middle_four not in middle_four_dict:
                    middle_four_dict[middle_four] = 1
                    image_idx = 1
                else:
                    middle_four_dict[middle_four] += 1
                    image_idx = middle_four_dict[middle_four]

            image_id = int(f"{middle_four}_{image_idx:03d}")
            img_height = data.get("imageHeight", 0)
            img_width = data.get("imageWidth", 0)

            if 'shapes' in data:
                coco_image = {
                    "file_name": new_jpg_name,
                    "height": img_height,
                    "width": img_width,
                    "id": image_id
                }
                coco_images.append(coco_image)

                for shape in data['shapes']:
                    label = shape['label']
                    if label == 'ALC条板':
                        print(f"Label: {label}")
                        continue
                    
                    category_id = shape['group_id']
                    # category_id = 3 if category_id == 5 else (category_id-1) 
                    # category_id = 4 if category_id == 5 else (category_id) 
                    category_name = shape['label']
                    if category_name not in category_set:
                        coco_categories.append({
                            "id": category_id,
                            "name": category_name
                        })
                        category_set.add(category_name)
                    
                    # 使用 pycocotools 计算多边形面积
                    points = shape['points']
                    # COCO segmentation 格式需要一维列表
                    segmentation = [coord for point in points for coord in point]
                    
                    # print(type(img_height), type(img_width))
                    # print(type(segmentation), type(segmentation[0]), segmentation)
                    # print(np.array(segmentation).shape)
                    # print(np.array(segmentation).reshape(-1, 2).shape)
                    # print(np.array(segmentation).reshape(-1, 2))
                    # print(type(np.array(segmentation).reshape(-1, 2)))

                    rle = mask.frPyObjects(np.array([segmentation], dtype=np.float64), img_height, img_width)
                    area = float(mask.area(rle)[0])

                    x_coords = [point[0] for point in shape['points']]
                    y_coords = [point[1] for point in shape['points']]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    width = x_max - x_min
                    height = y_max - y_min
                    annotation_id += 1

                    coco_annotations.append({
                        "id": annotation_id,
                        "image_id": coco_image["id"],
                        "category_id": category_id,
                        "bbox": [x_min, y_min, width, height],
                        "area": area,
                        "segmentation": segmentation,
                        "iscrowd": 0
                    })
                    
# 保存 COCO 格式的 json（每张图片一个 json 文件）
coco_json = {
    "images": coco_images,
    "annotations": coco_annotations,
    "categories": coco_categories
}

coco_json_path = os.path.join(labels_folder, f'wuliao_{data_type}.json')
with open(coco_json_path, 'w', encoding='utf-8') as coco_f:
    json.dump(coco_json, coco_f, ensure_ascii=False, indent=2)
