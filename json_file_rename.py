import os

# Define the folder paths
folder = '/Users/jinyfeng/projects/ai-construction/wuliao_train_val_labels/'

def rename_files_in_folder(folder_path):
    try:
        for filename in os.listdir(folder_path):
            if not filename.lower().endswith('.json'):
                continue
            old_file_path = os.path.join(folder_path, filename)
            print(old_file_path)
            if os.path.isfile(old_file_path):
                # Remove the first 11 characters from the filename
                new_filename = filename.replace('.json', '.txt')
                new_file_path = os.path.join(folder_path, new_filename)
                print(new_file_path)
                os.rename(old_file_path, new_file_path)
                print(f"Renamed: {old_file_path} -> {new_file_path}")
    except Exception as e:
        print(f"Error processing folder {folder_path}: {e}")

# Process each folder
rename_files_in_folder(folder)