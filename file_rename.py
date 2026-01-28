import os

folder_path = '/home/common_datas/jinyfeng/datas/suidao/safe_test/v2/'  # 修改为你的文件夹路径
folder_path = '/home/common_datas/jinyfeng/datas/suidao/safe_det/xiajingkou16_20260120'
folder_path = '/home/common_datas/jinyfeng/datas/suidao/safe_det/xiajingkou16_20260121'


# folder_path = '/home/common_datas/jinyfeng/datas/suidao/guanpian_det/'  # 修改为你的文件夹路径


for filename in os.listdir(folder_path):
    # if filename.lower().endswith('.jpg'):
    if filename.lower().endswith('.mp4'):
        if '$' in filename:
            # new_name = filename.split('$', 1)[1]
            new_name = filename.split('$_', 1)[1]
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_name)
            os.rename(old_path, new_path)
            print(f'Renamed: {filename} -> {new_name}')