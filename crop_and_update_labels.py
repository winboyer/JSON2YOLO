#!/usr/bin/env python3
"""
根据scale_person_bbox获取的新坐标进行图像裁剪，
同时更新标签为aqm和fgmj在新图像中的坐标位置
"""

import os
import json
import cv2
import numpy as np
from PIL import Image
from pathlib import Path


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


def crop_image_and_update_labels(image_path, json_path, output_dir, crop_ratio=0.1):
    """
    根据scale_person_bbox获取的新坐标进行图像裁剪，
    同时更新标签为aqm和fgmj在新图像中的坐标位置
    
    Args:
        image_path (str): 原始图像路径
        json_path (str): 对应的JSON标注文件路径
        output_dir (str): 输出目录
        crop_ratio (float): 裁剪比例，用于扩展裁剪区域
    """
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    img_height, img_width = image.shape[:2]
    
    # 读取JSON标注文件
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取原始图像尺寸
    if 'imageWidth' in data and 'imageHeight' in data:
        orig_img_width = data['imageWidth']
        orig_img_height = data['imageHeight']
    else:
        # 如果没有指定图像尺寸，则使用实际图像尺寸
        orig_img_width = img_width
        orig_img_height = img_height
    
    # 处理每个标注对象
    updated_shapes = []
    person_boxes = []  # 存储person类别的边界框
    
    if 'shapes' in data:
        for shape in data['shapes']:
            label = shape.get('label', '').lower()
            points = shape.get('points', [])
            
            # 如果是矩形框，计算边界框坐标
            if len(points) >= 2:
                x_coords = [point[0] for point in points]
                y_coords = [point[1] for point in points]
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                # 如果是person类别，应用缩放操作
                if label == 'person':
                    x_min_new, y_min_new, x_max_new, y_max_new = scale_person_bbox(
                        x_min, y_min, x_max, y_max, orig_img_width, orig_img_height
                    )
                    person_boxes.append({
                        'original': (x_min, y_min, x_max, y_max),
                        'scaled': (x_min_new, y_min_new, x_max_new, y_max_new),
                        'label': label
                    })
                else:
                    # 其他类别保持原样
                    updated_shapes.append(shape)
    
    # 如果有person框，进行裁剪
    if person_boxes:
        # 使用第一个person框作为参考进行裁剪
        # 或者可以考虑所有person框的合并区域
        first_person_box = person_boxes[0]['scaled']
        x_min_crop, y_min_crop, x_max_crop, y_max_crop = first_person_box
        
        # 扩展裁剪区域
        width = x_max_crop - x_min_crop
        height = y_max_crop - y_min_crop
        expand_width = int(width * crop_ratio)
        expand_height = int(height * crop_ratio)
        
        # 计算新的裁剪区域
        x_min_final = max(0, int(x_min_crop - expand_width))
        y_min_final = max(0, int(y_min_crop - expand_height))
        x_max_final = min(img_width, int(x_max_crop + expand_width))
        y_max_final = min(img_height, int(y_max_crop + expand_height))
        
        # 执行裁剪
        cropped_image = image[y_min_final:y_max_final, x_min_final:x_max_final]
        
        # 保存裁剪后的图像
        image_filename = Path(image_path).name
        cropped_image_path = os.path.join(output_dir, f"cropped_{image_filename}")
        cv2.imwrite(cropped_image_path, cropped_image)
        
        # 更新标签文件中的坐标
        # 重新计算所有标注框在新图像中的坐标
        updated_shapes = []
        if 'shapes' in data:
            for shape in data['shapes']:
                label = shape.get('label', '').lower()
                points = shape.get('points', [])
                
                # 如果是矩形框，计算边界框坐标
                if len(points) >= 2:
                    x_coords = [point[0] for point in points]
                    y_coords = [point[1] for point in points]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    # 如果是aqm或fgmj类别，更新坐标
                    if label in ['aqm', 'fgmj']:
                        # 计算在新图像中的相对坐标
                        new_x_min = max(0, x_min - x_min_final)
                        new_y_min = max(0, y_min - y_min_final)
                        new_x_max = min(cropped_image.shape[1], x_max - x_min_final)
                        new_y_max = min(cropped_image.shape[0], y_max - y_min_final)
                        
                        # 更新points
                        new_points = [
                            [new_x_min, new_y_min],
                            [new_x_max, new_y_max]
                        ]
                        
                        # 创建新的shape
                        new_shape = shape.copy()
                        new_shape['points'] = new_points
                        
                        # 更新边界框坐标
                        new_shape['bbox'] = {
                            'x': new_x_min,
                            'y': new_y_min,
                            'width': new_x_max - new_x_min,
                            'height': new_y_max - new_y_min
                        }
                        
                        updated_shapes.append(new_shape)
                    else:
                        # 其他类别保持原样
                        updated_shapes.append(shape)
        
        # 保存更新后的JSON文件
        json_filename = Path(json_path).name
        updated_json_path = os.path.join(output_dir, f"cropped_{json_filename}")
        
        # 更新shapes
        data['shapes'] = updated_shapes
        
        # 更新图像尺寸为裁剪后的尺寸
        data['imageWidth'] = cropped_image.shape[1]
        data['imageHeight'] = cropped_image.shape[0]
        
        with open(updated_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"已裁剪图像并更新标签:")
        print(f"  原始图像: {image_path}")
        print(f"  裁剪后图像: {cropped_image_path}")
        print(f"  更新后的JSON: {updated_json_path}")
        print(f"  裁剪区域: ({x_min_final}, {y_min_final}) 到 ({x_max_final}, {y_max_final})")
        
        return cropped_image_path, updated_json_path
    
    else:
        # 如果没有person框，直接复制图像和JSON文件
        image_filename = Path(image_path).name
        json_filename = Path(json_path).name
        
        # 复制图像
        copied_image_path = os.path.join(output_dir, f"cropped_{image_filename}")
        cv2.imwrite(copied_image_path, image)
        
        # 复制JSON文件
        copied_json_path = os.path.join(output_dir, f"cropped_{json_filename}")
        with open(json_path, 'r', encoding='utf-8') as src:
            with open(copied_json_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        print(f"未检测到person框，直接复制图像和JSON文件:")
        print(f"  原始图像: {image_path}")
        print(f"  复制图像: {copied_image_path}")
        print(f"  复制JSON: {copied_json_path}")
        
        return copied_image_path, copied_json_path


def batch_crop_and_update(input_image_dir, input_json_dir, output_dir, crop_ratio=0.1):
    """
    批量处理图像和JSON文件
    
    Args:
        input_image_dir (str): 输入图像目录
        input_json_dir (str): 输入JSON目录
        output_dir (str): 输出目录
        crop_ratio (float): 裁剪比例
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有JSON文件
    json_files = [f for f in os.listdir(input_json_dir) if f.endswith('.json')]
    
    print(f"开始批量处理 {len(json_files)} 个JSON文件...")
    
    for json_file in json_files:
        json_path = os.path.join(input_json_dir, json_file)
        image_filename = json_file.replace('.json', '.jpg')
        image_path = os.path.join(input_image_dir, image_filename)
        
        if os.path.exists(image_path):
            try:
                cropped_image_path, updated_json_path = crop_image_and_update_labels(
                    image_path, json_path, output_dir, crop_ratio
                )
            except Exception as e:
                print(f"处理文件 {json_file} 时出错: {e}")
        else:
            print(f"未找到对应的图像文件: {image_path}")


if __name__ == "__main__":
    # 示例用法
    import argparse
    
    parser = argparse.ArgumentParser(description='根据scale_person_bbox获取的新坐标进行图像裁剪，同时更新标签')
    parser.add_argument('--image_dir', type=str, required=True, help='图像文件夹路径')
    parser.add_argument('--json_dir', type=str, required=True, help='JSON标注文件夹路径')
    parser.add_argument('--output_dir', type=str, required=True, help='输出文件夹路径')
    parser.add_argument('--crop_ratio', type=float, default=0.1, help='裁剪比例 (默认: 0.1)')
    
    args = parser.parse_args()
    
    print("开始批量处理图像和JSON文件...")
    print(f"输入图像目录: {args.image_dir}")
    print(f"输入JSON目录: {args.json_dir}")
    print(f"输出目录: {args.output_dir}")
    print(f"裁剪比例: {args.crop_ratio}")
    
    batch_crop_and_update(args.image_dir, args.json_dir, args.output_dir, args.crop_ratio)
    
    print("批量处理完成!")
