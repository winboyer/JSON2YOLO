#!/usr/bin/env python3
"""
读取图像文件夹和JSON标注文件夹，提取标注坐标位置
"""

import os
import json
import argparse
from pathlib import Path
from PIL import Image
import cv2
import time

def scale_person_bbox(x_min, y_min, x_max, y_max, img_width, img_height):
    """
    将类别为person的边界框高度放大1.5倍，宽度放大2倍，超出图像范围的部分忽略
    
    Args:
        x_min, y_min, x_max, y_max: 原始边界框坐标
        img_width, img_height: 图像宽度和高度
    
    Returns:
        新的边界框坐标 (x_min_new, y_min_new, x_max_new, y_max_new)
    """
    # 计算原始中心点
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    
    # 计算原始宽高
    width = x_max - x_min
    height = y_max - y_min
    
    # 放大后的宽高
    new_width = width * 2
    new_height = height * 1.5
    
    # 计算新的边界框坐标
    x_min_new = center_x - new_width / 2
    x_max_new = center_x + new_width / 2
    y_min_new = center_y - new_height / 2
    y_max_new = center_y + new_height / 2
    
    # 确保不超出图像边界
    x_min_new = max(0, x_min_new)
    x_max_new = min(img_width, x_max_new)
    y_min_new = max(0, y_min_new)
    y_max_new = min(img_height, y_max_new)
    
    return x_min_new, y_min_new, x_max_new, y_max_new

# 如果aqm或fgmj有标注，更新其坐标
def update_coords(obj_coords, person_ori_coords, person_new_coords):
    updated_coords = []
    for obj_bbox in obj_coords:
        x_min_obj, y_min_obj, x_max_obj, y_max_obj = obj_bbox
        updated = False
        for idx, (x_min_p, y_min_p, x_max_p, y_max_p) in enumerate(person_ori_coords):
            # 判断obj_bbox是否完全在person_ori_bbox内
            if (x_min_obj >= x_min_p and y_min_obj >= y_min_p and
                x_max_obj <= x_max_p and y_max_obj <= y_max_p):
                # 计算在原person框内的相对位置
                px0, py0, px1, py1 = x_min_p, y_min_p, x_max_p, y_max_p
                nx0, ny0, nx1, ny1 = person_new_coords[idx]
                pw, ph = px1 - px0, py1 - py0
                nw, nh = nx1 - nx0, ny1 - ny0
                # 相对比例
                rel_xmin = (x_min_obj - px0) / pw if pw > 0 else 0
                rel_ymin = (y_min_obj - py0) / ph if ph > 0 else 0
                rel_xmax = (x_max_obj - px0) / pw if pw > 0 else 0
                rel_ymax = (y_max_obj - py0) / ph if ph > 0 else 0
                # 映射到新person框
                x_min_new = nx0 + rel_xmin * nw
                y_min_new = ny0 + rel_ymin * nh
                x_max_new = nx0 + rel_xmax * nw
                y_max_new = ny0 + rel_ymax * nh
                updated_coords.append((x_min_new, y_min_new, x_max_new, y_max_new))
                print(f"    坐标 {obj_bbox} 属于person框 {person_ori_coords[idx]}，更新为 {updated_coords[-1]}")
                updated = True
                break
        if not updated:
            # 没有匹配person框，保持原坐标
            updated_coords.append(obj_bbox)
            print(f"    坐标 {obj_bbox} 未匹配到person框，保持不变")
    return updated_coords

# 如果aqm或fgmj有标注，更新其坐标
def update_coords_v1(obj_coord, person_new_coord):
        
    x_min_obj, y_min_obj, x_max_obj, y_max_obj = obj_coord
    
    # 计算在原person框内的相对位置
    nx0, ny0, nx1, ny1 = person_new_coord

    # 映射到新person框
    x_min_new = x_min_obj - nx0
    y_min_new = y_min_obj - ny0
    x_max_new = x_max_obj - nx0
    y_max_new = y_max_obj - ny0

    updated_coord = (x_min_new, y_min_new, x_max_new, y_max_new)
    
    return updated_coord

def read_image_and_json(image_folder, json_folder, image_save_folder, label_save_folder):
    """
    读取图像文件夹和JSON标注文件夹，提取标注的坐标位置
    
    Args:
        image_folder (str): 图像文件夹路径
        json_folder (str): JSON标注文件夹路径
    """
    
    # 检查文件夹是否存在
    if not os.path.exists(image_folder):
        print(f"错误: 图像文件夹 '{image_folder}' 不存在")
        return
    
    if not os.path.exists(json_folder):
        print(f"错误: JSON文件夹 '{json_folder}' 不存在")
        return

    if not os.path.exists(image_save_folder):
        os.makedirs(image_save_folder)
    if not os.path.exists(label_save_folder):
        os.makedirs(label_save_folder)
    
    # 获取所有JSON文件
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    
    if not json_files:
        print(f"警告: 在 '{json_folder}' 中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON标注文件")
    
    # 遍历每个JSON文件
    coco_images = []
    coco_annotations = []
    coco_categories = []
    category_set = set()
    annotation_id = 0
    coco_image_id = 0
    for json_file in json_files:
        json_path = os.path.join(json_folder, json_file)
        
        try:
            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n处理文件: {json_file}")
            
            # 获取图像尺寸
            img_width = None
            img_height = None
            if 'imageWidth' in data and 'imageHeight' in data:
                img_width = data['imageWidth']
                img_height = data['imageHeight']
                print(f"  图像尺寸: {img_width} x {img_height}")
            else:
                print("  警告: 图像尺寸信息缺失，跳过该文件")
                time.sleep(60)
                continue
            # 根据JSON格式提取坐标信息
            if 'shapes' in data:
                
                person_cnt = 0
                person_x1, person_x2 = 0, 0
                person_y1, person_y2 = 0, 0
                person_x1_new, person_y1_new, person_x2_new, person_y2_new = 0, 0, 0, 0
                for i, shape in enumerate(data['shapes']):
                    label = shape.get('label', 'unknown')
                    if label == 'person':
                        person_cnt += 1
                        points = shape.get('points', [])
                        x_coords = [point[0] for point in points]
                        y_coords = [point[1] for point in points]
                        person_x1, person_x2 = min(x_coords), max(x_coords)
                        person_y1, person_y2 = min(y_coords), max(y_coords)
                        
                        if img_width is not None and img_height is not None:
                            person_x1_new, person_y1_new, person_x2_new, person_y2_new = scale_person_bbox(person_x1, person_y1, person_x2, person_y2, img_width, img_height)
                        continue
                
                if person_cnt > 1:
                    print(f"  警告: person类别数量过多 ({person_cnt} 个)，跳过该文件")
                    continue

                coco_image_id += 1
                for i, shape in enumerate(data['shapes']):
                    label = shape.get('label', 'unknown')
                    label = label.lower()
                    group_id = shape.get('group_id', 'unknown')
                    points = shape.get('points', [])
                    x_coords = [point[0] for point in points]
                    y_coords = [point[1] for point in points]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    print(f"    标签: {label}")
                    print(f"    组ID: {group_id}")

                    if label == 'aqm':
                        aqm_ori_coord = (x_min, y_min, x_max, y_max)
                        aqm_new_coord = update_coords_v1(aqm_ori_coord, (person_x1_new, person_y1_new, person_x2_new, person_y2_new))
                        
                        if label != 'unknown' and group_id != 'unknown' and label not in category_set:
                            coco_categories.append({
                                "id": group_id,
                                "name": label
                            })
                            category_set.add(label)
                        
                        coco_annotations.append({
                            "id": annotation_id + 1,
                            "image_id": coco_image_id,
                            "category_id": group_id,
                            "bbox": [px0, py0, px1 - px0, py1 - py0],
                            "area": (px1 - px0) * (py1 - py0),
                            "segmentation": [],
                            "iscrowd": 0
                        })
                        annotation_id += 1

                    elif label == 'fgmj':
                        fgmj_ori_coord = (x_min, y_min, x_max, y_max)
                        fgmj_new_coord = update_coords_v1(fgmj_ori_coord, (person_x1_new, person_y1_new, person_x2_new, person_y2_new))
                        
                        if label != 'unknown' and group_id != 'unknown' and label not in category_set:
                            coco_categories.append({
                                "id": group_id,
                                "name": label
                            })
                            category_set.add(label)
                        
                        coco_annotations.append({
                            "id": annotation_id + 1,
                            "image_id": coco_image_id,
                            "category_id": group_id,
                            "bbox": [px0, py0, px1 - px0, py1 - py0],
                            "area": (px1 - px0) * (py1 - py0),
                            "segmentation": [],
                            "iscrowd": 0
                        })
                        annotation_id += 1
                    # person类别处理
                    elif label == 'person':
                        person_new_coords = (person_x1_new, person_y1_new, person_x2_new, person_y2_new)
                        
                        image_filename = json_file.replace('.json', '.jpg')
                        image_path = os.path.join(image_folder, image_filename)
                        if not os.path.exists(image_path):
                            print(f"  警告: 图像文件 '{image_filename}' 不存在，跳过显示")
                        
                        image = cv2.imread(image_path)

                        image_crop = image[int(person_y1_new):int(person_y2_new), int(person_x1_new):int(person_x2_new)]
                        new_height, new_width = image_crop.shape[:2]
                        # new_name = f"{image_folder.split('/')[-1]}_{image_filename.replace('.jpg', '')}_{idx+1}.jpg"
                        new_name = f"{image_folder.split('/')[-1]}_{image_filename}"
                        print(new_name)
                        # cv2.rectangle(image_crop, (int(aqm_new_coord[0]), int(aqm_new_coord[1])), 
                        #               (int(aqm_new_coord[2]), int(aqm_new_coord[3])), (0, 255, 0), 2)
                        # cv2.rectangle(image_crop, (int(fgmj_new_coord[0]), int(fgmj_new_coord[1])), 
                        #               (int(fgmj_new_coord[2]), int(fgmj_new_coord[3])), (255, 0, 0), 2)
                        # cv2.imshow("Image", image)
                        # cv2.waitKey(0)
                        # cv2.destroyAllWindows()
                        # cv2.imwrite(f"updated_{image_filename}", image_crop)
                        time.sleep(120)
                        cv2.imwrite(os.path.join(image_save_folder, new_name), image_crop)
            
                        coco_image = {
                            "file_name": new_name,
                            "height": new_height,
                            "width": new_width,
                            "id": coco_image_id
                        }
                        coco_images.append(coco_image)

            coco_json = {
                "images": coco_images,
                "annotations": coco_annotations,
                "categories": coco_categories
            }
            coco_json_path = os.path.join(label_save_folder, f'{new_name.split(".")[0]}.json')
            with open(coco_json_path, 'w') as f:
                json.dump(coco_json, f)
        except Exception as e:
            print(f"  处理文件 {json_file} 时出错: {e}")
            continue
    
    

def main():
    parser = argparse.ArgumentParser(description='读取图像文件夹和JSON标注文件夹，提取标注坐标位置')
    parser.add_argument('--image_folder', type=str, default='/home/jinyfeng/datas/suidao/16f3d2dbf72b7506c8252dcf147f6758_raw', help='图像文件夹路径')
    parser.add_argument('--json_folder', type=str, default='/home/jinyfeng/datas/suidao/label_16f3d2dbf72b7506c8252dcf147f6758_raw', help='JSON标注文件夹路径')
    parser.add_argument('--image_save_folder', type=str, default='/home/jinyfeng/datas/suidao/new_16f3d2dbf72b7506c8252dcf147f6758_raw_crop', help='处理后图像保存文件夹路径')
    parser.add_argument('--label_save_folder', type=str, default='/home/jinyfeng/datas/suidao/new_label_16f3d2dbf72b7506c8252dcf147f6758_raw_crop', help='处理后JSON保存文件夹路径')

    args = parser.parse_args()
    
    print("开始读取图像和JSON标注数据...")
    print(f"图像文件夹: {args.image_folder}")
    print(f"JSON文件夹: {args.json_folder}")
    
    read_image_and_json(args.image_folder, args.json_folder, args.image_save_folder, args.label_save_folder)
    
    print("\n处理完成!")

if __name__ == "__main__":
    main()
