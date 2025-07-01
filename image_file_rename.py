import os

# Define the folder paths
folders = [
    # "/Users/jinyfeng/projects/ai-construction/20250508",
    # "/Users/jinyfeng/projects/ai-construction/20250509",
    # "/Users/jinyfeng/projects/ai-construction/20250510",
    # "/Users/jinyfeng/projects/ai-construction/20250511",
    # "/Users/jinyfeng/projects/ai-construction/20250512"
]

def rename_files_in_folder(folder_path):
    try:
        for filename in os.listdir(folder_path):
            if not filename.lower().endswith('.jpg'):
                continue
            old_file_path = os.path.join(folder_path, filename)
            if os.path.isfile(old_file_path):
                # Remove the first 11 characters from the filename
                new_filename = filename[11:]
                new_file_path = os.path.join(folder_path, new_filename)
                os.rename(old_file_path, new_file_path)
                print(f"Renamed: {old_file_path} -> {new_file_path}")
    except Exception as e:
        print(f"Error processing folder {folder_path}: {e}")

# Process each folder
for folder in folders:
    rename_files_in_folder(folder)