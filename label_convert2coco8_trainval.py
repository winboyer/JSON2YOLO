import os
import json
import shutil
import random

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
    'F:/BaiduNetdiskDownload/182_20250603',
]

# 创建一个名为 "施工物料训练数据" 的文件夹
# train_val_images_folder = '/Users/jinyfeng/projects/ai-construction/wuliao_train_val_images'
# train_val_labels_folder = '/Users/jinyfeng/projects/ai-construction/wuliao_train_val_labels'

train_images_folder = 'D:/jinyfeng/datas/shajiangche/train_images'
train_labels_folder = 'D:/jinyfeng/datas/shajiangche/train_labels'

val_images_folder = 'D:/jinyfeng/datas/shajiangche/val_images'
val_labels_folder = 'D:/jinyfeng/datas/shajiangche/val_labels'

if not os.path.exists(train_images_folder):
    os.makedirs(train_images_folder)
if not os.path.exists(train_labels_folder):
    os.makedirs(train_labels_folder)
if not os.path.exists(val_images_folder):
    os.makedirs(val_images_folder)
if not os.path.exists(val_labels_folder):
    os.makedirs(val_labels_folder) 

# 遍历每个文件夹路径
for folder_path in folder_paths:
    print(f"Processing folder: {folder_path}")
    # 获取文件夹名称
    folder_name = os.path.basename(folder_path)

    # 获取所有jpg文件名（不含扩展名）
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    random.shuffle(all_files)
    split_idx = int(len(all_files) * 0.9)
    train_files = all_files[:split_idx]
    val_files = all_files[split_idx:]
    print(f"Train files: {len(train_files)}, Val files: {len(val_files)}")

    for file_name in train_files:
        file_path = os.path.join(folder_path, file_name)
        jpg_name = f"{file_name.replace('.json', '.jpg')}"
        jpg_file_path = os.path.join(folder_path, jpg_name)
        new_jpg_name = f"{folder_name}_{jpg_name}"

        new_jpg_path = os.path.join(train_images_folder, new_jpg_name)
        shutil.copy(jpg_file_path, new_jpg_path)
        new_file_path = os.path.join(train_labels_folder, new_jpg_name.replace('.jpg', '.json'))
        shutil.copy(file_path, new_file_path)

    for file_name in val_files:
        file_path = os.path.join(folder_path, file_name)
        jpg_name = f"{file_name.replace('.json', '.jpg')}"
        jpg_file_path = os.path.join(folder_path, jpg_name)
        new_jpg_name = f"{folder_name}_{jpg_name}"

        new_jpg_path = os.path.join(val_images_folder, new_jpg_name)
        shutil.copy(jpg_file_path, new_jpg_path)
        new_file_path = os.path.join(val_labels_folder, new_jpg_name.replace('.jpg', '.json'))
        shutil.copy(file_path, new_file_path)

    # # 遍历文件夹中的所有 JSON 文件
    # for file_name in os.listdir(folder_path):
    #     if file_name.endswith('.json'):
    #         file_path = os.path.join(folder_path, file_name)
    #         jpg_name = f"{file_name.replace('.json', '.jpg')}"
    #         jpg_file_path = os.path.join(folder_path, jpg_name)
    #         new_jpg_name = f"{folder_name}_{jpg_name}"

    #         new_jpg_path = os.path.join(train_val_images_folder, new_jpg_name)
    #         shutil.copy(jpg_file_path, new_jpg_path)
    #         new_file_path = os.path.join(train_val_labels_folder, new_jpg_name.replace('.jpg', '.json'))
    #         shutil.copy(file_path, new_file_path)

            # # 打开并读取 JSON 文件
            # with open(file_path, 'r', encoding='utf-8') as f:
            #     data = json.load(f)
            
            # # 提取 shapes 中 points 的值
            # if 'shapes' in data:
            #     for shape in data['shapes']:
            #         label = shape['label']
            #         # if label == 'ALC条板' or label == 'baowenban':
            #         #     print(f"Label: {label}")
            #         #     continue
            #         if label == 'ALC条板':
            #             print(f"Label: {label}")
            #             continue
            #         elif label == 'baowenban':
            #             print(f"Label: {label}")
            #         if 'group_id' in shape:
            #             group_id = shape['group_id']
            #             # print(type(group_id))
            #             # print(f"File: {file_name}, Group ID: {group_id}")
            #         if 'points' in shape:
            #             x_coords = [point[0] for point in shape['points']]
            #             y_coords = [point[1] for point in shape['points']]
            #             x_min, x_max = min(x_coords), max(x_coords)
            #             y_min, y_max = min(y_coords), max(y_coords)
            #             x_min, x_max = int(x_min), int(x_max)
            #             y_min, y_max = int(y_min), int(y_max)
            #             # print(f"File: {file_name}, X_min: {x_min}, X_max: {x_max}, Y_min: {y_min}, Y_max: {y_max}")

            #             # 将 group_id 和坐标写入到 txt 文件中
            #             txt_file = new_jpg_name.replace('.jpg', '.txt')
            #             output_file = os.path.join(train_val_labels_folder, txt_file)
            #             with open(output_file, 'a', encoding='utf-8') as out_f:
            #                 # if group_id != 5:
            #                 #     group_id -= 1
            #                 # else:
            #                 #     group_id = 3

            #                 group_id -= 1
            #                 out_f.write(str(group_id)+f" "+f"{x_min} {y_min} {x_max} {y_max}\n")

