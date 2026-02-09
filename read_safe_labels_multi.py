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
    new_width = width * 1.2
    new_height = height * 1.2
    
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
def update_coords_v1(obj_coord, person_new_coord):
        
    x_min_obj, y_min_obj, x_max_obj, y_max_obj = obj_coord
    
    # 计算在原person框内的相对位置
    nx0, ny0, nx1, ny1 = person_new_coord

    # 映射到新person框
    x_min_new = x_min_obj - nx0
    y_min_new = y_min_obj - ny0
    x_max_new = x_max_obj - nx0
    y_max_new = y_max_obj - ny0

    return x_min_new, y_min_new, x_max_new, y_max_new
    
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
                person_cnt = 0
                person_x1, person_x2 = 0, 0
                person_y1, person_y2 = 0, 0
                person_x1_new, person_y1_new, person_x2_new, person_y2_new = 0, 0, 0, 0
                
                new_crop_height, new_crop_width = 0, 0
                image_filename = json_file.replace('.json', '.jpg')
                image_path = os.path.join(image_folder, image_filename)
                if not os.path.exists(image_path):
                    print(f"  警告: 图像文件 '{image_filename}' 不存在，跳过显示")
                    time.sleep(60)
                    continue

                group_list = []
                # 初始化一个字典，用于根据group_id存储new_crop_height, new_crop_width, image_crop, new_name等信息
                group_info_list = []
                for i, shape in enumerate(data['shapes']):
                    label = shape.get('label', 'unknown')
                    label = label.lower()
                    # person类别处理
                    if 'person' in label:
                        person_cnt += 1
                        group_id = label.split('-')[1]
                        # print('group_id=======', group_id)
                        
                        points = shape.get('points', [])
                        x_coords = [point[0] for point in points]
                        y_coords = [point[1] for point in points]
                        person_x1, person_x2 = min(x_coords), max(x_coords)
                        person_y1, person_y2 = min(y_coords), max(y_coords)
                        person_width = person_x2-person_x1
                        
                        # 如果person的宽度低于61，则舍弃
                        if person_width < 61:       # 63/65/75
                            print(f"{json_file} {label} width is small !")
                            continue
                        
                        group_list.append(group_id)                        
                        
                        if img_width is not None and img_height is not None:
                            person_x1_new, person_y1_new, person_x2_new, person_y2_new = scale_person_bbox(person_x1, person_y1, person_x2, person_y2, img_width, img_height)                            
                            person_new_coords = (person_x1_new, person_y1_new, person_x2_new, person_y2_new)
                            image = cv2.imread(image_path)
                            image_crop = image[int(person_y1_new):int(person_y2_new), int(person_x1_new):int(person_x2_new)]
                            new_crop_height, new_crop_width = image_crop.shape[:2]
                            
                            # new_name = f"{image_folder.split('/')[-1]}_{image_filename.replace('.jpg', '')}_{idx+1}.jpg"
                            new_name = f"{image_folder.split('/')[-1]}_{image_filename.replace('.jpg', "_"+str(group_id))}.jpg"
                            # print('new_name=======', new_name)
                            
                            group_info_list.append({
                                "group_id": group_id,
                                "new_crop_height": new_crop_height,
                                "new_crop_width": new_crop_width,
                                "image_crop": image_crop,
                                "new_name": new_name,
                                "person_new_coords": person_new_coords
                            })

                            # cv2.rectangle(image_crop, (int(aqm_new_coord[0]), int(aqm_new_coord[1])), 
                            #               (int(aqm_new_coord[2]), int(aqm_new_coord[3])), (0, 255, 0), 2)
                            # cv2.rectangle(image_crop, (int(fgmj_new_coord[0]), int(fgmj_new_coord[1])), 
                            #               (int(fgmj_new_coord[2]), int(fgmj_new_coord[3])), (255, 0, 0), 2)
                            # cv2.imshow("Image", image)
                            # cv2.waitKey(0)
                            # cv2.destroyAllWindows()
                            # cv2.imwrite(f"updated_{image_filename}", image_crop)
                            # time.sleep(120)
                            # cv2.imwrite(os.path.join(image_save_folder, new_name), image_crop)                        
                
                print(f'group_list:{group_list}')
                # time.sleep(120)

                bboxes = []                
                for i, shape in enumerate(data['shapes']):
                    label = shape.get('label', 'unknown')
                    label = label.lower()

                    group_id = label.split('-')[1]
                    print(f"    标签: {label}")
                    print(f"    组ID: {group_id}")
                    # cls = int(group_id) - 1
                    points = shape.get('points', [])
                    x_coords = [point[0] for point in points]
                    y_coords = [point[1] for point in points]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    group_info = next((info for info in group_info_list if info["group_id"] == group_id), None)
                    if group_info is None:
                        # print(f"    警告: 没有找到对应的group_id {group_id} 的person信息，跳过该框")
                        # time.sleep(120)
                        continue

                    if 'aqm' in label:
                        if group_id in group_list:
                            print(f"{group_id} in {group_list}")
                            
                            new_crop_height = group_info["new_crop_height"]
                            new_crop_width = group_info["new_crop_width"]
                            image_crop = group_info["image_crop"]
                            new_name = group_info["new_name"]
                            person_new_coords = group_info["person_new_coords"]
                            # print(f"    person_new_coords: {person_new_coords}")
                            # time.sleep(120)
                            aqm_ori_coord = (x_min, y_min, x_max, y_max)
                            # print(f"    aqm_ori_coord: {aqm_ori_coord}")
                            x_min_new, y_min_new, x_max_new, y_max_new = update_coords_v1(aqm_ori_coord, (person_new_coords[0], person_new_coords[1], person_new_coords[2], person_new_coords[3]))
                            # print(f"    aqm_new_coord: {(x_min_new, y_min_new, x_max_new, y_max_new)}")
                            # if image_crop is not None:
                            #     cv2.rectangle(image_crop, (int(x_min_new), int(y_min_new)), 
                            #                   (int(x_max_new), int(y_max_new)), (0, 255, 0), 2)
                            #     cv2.imwrite(f"debug_aqm_{image_filename}", image_crop)
                            #     time.sleep(120)
                            box = np.array([x_min_new, y_min_new, x_max_new-x_min_new, y_max_new-y_min_new], dtype=np.float64)
                            # print(f"    box (xywh): {box}")
                            box[:2] += box[2:] / 2  # xy top-left corner to center
                            # print(f"    box (cxcywh): {box}")
                            box[[0, 2]] /= new_crop_width  # normalize x
                            box[[1, 3]] /= new_crop_height  # normalize y
                            if box[2] <= 0 or box[3] <= 0:  # if w <= 0 and h <= 0
                                print(f"    警告: 更新后aqm框无效，跳过该框")
                                time.sleep(60)
                                continue
                            if box[0] > 1 or box[0] < 0 or box[1] > 1 or box[1] < 0:
                                print(f"    警告: 更新后aqm框坐标超出范围，跳过该框")
                                # print(f"    box: {box}", f"new_crop_width: {new_crop_width}", f"new_crop_height: {new_crop_height}")
                                time.sleep(60)
                                continue
                            
                            cls = 0
                            box = [cls] + box.tolist()
                            # print(f"Box: {box}")
                            if box not in bboxes:
                                bboxes.append(box)

                            cv2.imwrite(os.path.join(image_save_folder, new_name), image_crop)

                            label_save_path = os.path.join(label_save_folder, new_name.replace('.jpg', '.txt'))
                            with open(label_save_path, "a+") as file:
                                line = (*(box),)  # cls, box or segments
                                file.write(("%g " * len(line)).rstrip() % line + "\n")
                                # for i in range(len(bboxes)):
                                #     line = (*(bboxes[i]),)  # cls, box or segments
                                #     file.write(("%g " * len(line)).rstrip() % line + "\n")
                        
                    elif 'fgmj' in label:
                        if group_id in group_list:
                            print(f"{group_id} in {group_list}")
                            # time.sleep(120)

                            new_crop_height = group_info["new_crop_height"]
                            new_crop_width = group_info["new_crop_width"]
                            image_crop = group_info["image_crop"]
                            new_name = group_info["new_name"]
                            person_new_coords = group_info["person_new_coords"]

                            fgmj_ori_coord = (x_min, y_min, x_max, y_max)
                            x_min_new, y_min_new, x_max_new, y_max_new  = update_coords_v1(fgmj_ori_coord, (person_new_coords[0], person_new_coords[1], person_new_coords[2], person_new_coords[3]))
                            # if image_crop is not None:
                            #     cv2.rectangle(image_crop, (int(x_min_new), int(y_min_new)), 
                            #                   (int(x_max_new), int(y_max_new)), (0, 255, 0), 2)
                            #     cv2.imwrite(f"debug_fgmj_{image_filename}", image_crop)
                            #     time.sleep(120)
                            box = np.array([x_min_new, y_min_new, x_max_new-x_min_new, y_max_new-y_min_new], dtype=np.float64)
                            box[:2] += box[2:] / 2  # xy top-left corner to center
                            box[[0, 2]] /= new_crop_width  # normalize x
                            box[[1, 3]] /= new_crop_height  # normalize y
                            if box[2] <= 0 or box[3] <= 0:  # if w <= 0 and h <= 0
                                print(f"    警告: 更新后fgmj框无效，跳过该框")
                                time.sleep(60)
                                continue
                            if box[0] > 1 or box[0] < 0 or box[1] > 1 or box[1] < 0:
                                print(f"    警告: 更新后fgmj框坐标超出范围，跳过该框")
                                print(f"    box: {box}")
                                time.sleep(60)
                                continue
                            cls = 1
                            box = [cls] + box.tolist()
                            # print(f"Box: {box}")
                            # if box not in bboxes:
                            #     bboxes.append(box)
                            
                            cv2.imwrite(os.path.join(image_save_folder, new_name), image_crop)
                            
                            label_save_path = os.path.join(label_save_folder, new_name.replace('.jpg', '.txt'))
                            with open(label_save_path, "a+") as file:
                                line = (*(box),)  # cls, box or segments
                                file.write(("%g " * len(line)).rstrip() % line + "\n")
                                # for i in range(len(bboxes)):
                                #     line = (*(bboxes[i]),)  # cls, box or segments
                                #     file.write(("%g " * len(line)).rstrip() % line + "\n")


        except Exception as e:
            print(f"  处理文件 {json_file} 时出错: {e}")
            time.sleep(60)
            continue
    
    

def main():
    parser = argparse.ArgumentParser(description='读取图像文件夹和JSON标注文件夹，提取标注坐标位置')

    parser.add_argument('--image_folder', type=str, default='/home/jinyfeng/datas/suidao/safe_det/2897f7c79704abf07bf74d05ed0e585a_raw', help='图像文件夹路径')
    parser.add_argument('--json_folder', type=str, default='/home/jinyfeng/datas/suidao/safe_det/labels_2897f7c79704abf07bf74d05ed0e585a_raw_v2', help='JSON标注文件夹路径')
    parser.add_argument('--image_save_folder', type=str, default='/home/jinyfeng/datas/suidao/safe_det/new_2897f7c79704abf07bf74d05ed0e585a_raw_crop', help='处理后图像保存文件夹路径')
    parser.add_argument('--label_save_folder', type=str, default='/home/jinyfeng/datas/suidao/safe_det/new_labels_2897f7c79704abf07bf74d05ed0e585a_raw_crop', help='处理后JSON保存文件夹路径')
    
    
    args = parser.parse_args()
    
    print("开始读取图像和JSON标注数据...")
    print(f"图像文件夹: {args.image_folder}")
    print(f"JSON文件夹: {args.json_folder}")
    
    read_image_and_json(args.image_folder, args.json_folder, args.image_save_folder, args.label_save_folder)
    
    print("\n处理完成!")

if __name__ == "__main__":
    main()
