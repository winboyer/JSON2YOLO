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
import numpy as np
import shutil

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
                guanpian_cnt = 0
                
                image_filename = json_file.replace('.json', '.jpg')
                image_path = os.path.join(image_folder, image_filename)
                if not os.path.exists(image_path):
                    print(f"  警告: 图像文件 '{image_filename}' 不存在，跳过显示")
                    time.sleep(60)
                    continue

                for i, shape in enumerate(data['shapes']):
                    label = shape.get('label', 'unknown')
                    label = label.lower()
                    group_id = shape.get('group_id', 'unknown')
                    # 管片类别处理
                    if label == 'gp':
                        guanpian_cnt += 1
                
                if guanpian_cnt > 1:
                    print(f"  警告: guanpian类别数量过多 ({guanpian_cnt} 个)，跳过该文件")
                    time.sleep(60)
                    continue

                bboxes = []                
                for i, shape in enumerate(data['shapes']):
                    label = shape.get('label', 'unknown')
                    label = label.lower()
                    group_id = shape.get('group_id', 'unknown')
                    print(f"    标签: {label}")
                    print(f"    组ID: {group_id}")

                    # cls = int(group_id) - 1
                    points = shape.get('points', [])
                    x_coords = [point[0] for point in points]
                    y_coords = [point[1] for point in points]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    if label == 'gp':                        
                        box = np.array([x_min, y_min, x_max-x_min, y_max-y_min], dtype=np.float64)
                        box[:2] += box[2:] / 2  # xy top-left corner to center
                        box[[0, 2]] /= img_width  # normalize x
                        box[[1, 3]] /= img_height  # normalize y
                        if box[2] <= 0 or box[3] <= 0:  # if w <= 0 and h <= 0
                            print(f"    警告: 更新后gp框无效，跳过该框")
                            time.sleep(60)
                            continue
                        
                        cls = 0
                        box = [cls] + box.tolist()
                        # print(f"Box: {box}")
                        if box not in bboxes:
                            bboxes.append(box)

                image_save_path = os.path.join(image_save_folder, image_filename)
                shutil.copyfile(image_path, image_save_path)
                label_save_path = os.path.join(label_save_folder, image_filename.replace('.jpg', '.txt'))
                with open(label_save_path, "a+") as file:
                    for i in range(len(bboxes)):
                        line = (*(bboxes[i]),)  # cls, box or segments
                        file.write(("%g " * len(line)).rstrip() % line + "\n")

        except Exception as e:
            print(f"  处理文件 {json_file} 时出错: {e}")
            time.sleep(60)
            continue
    

def main():
    parser = argparse.ArgumentParser(description='读取图像文件夹和JSON标注文件夹，提取标注坐标位置')
    parser.add_argument('--image_folder', type=str, default='/home/common_datas/jinyfeng/datas/suidao/guanpian_det/20260126/S20260126174446_E20260126174750', help='图像文件夹路径')
    parser.add_argument('--json_folder', type=str, default='/home/common_datas/jinyfeng/datas/suidao/guanpian_det/20260126/label_S20260126174446_E20260126174750', help='JSON标注文件夹路径')
    parser.add_argument('--image_save_folder', type=str, default='/home/jinyfeng/datas/suidao/guanpian_det/20260126/new_images_S20260126174446_E20260126174750', help='处理后图像保存文件夹路径')
    parser.add_argument('--label_save_folder', type=str, default='/home/jinyfeng/datas/suidao/guanpian_det/20260126/new_label_S20260126174446_E20260126174750', help='处理后JSON保存文件夹路径')

    args = parser.parse_args()
    
    print("开始读取图像和JSON标注数据...")
    print(f"图像文件夹: {args.image_folder}")
    print(f"JSON文件夹: {args.json_folder}")
    
    read_image_and_json(args.image_folder, args.json_folder, args.image_save_folder, args.label_save_folder)
    
    print("\n处理完成!")

if __name__ == "__main__":
    main()
