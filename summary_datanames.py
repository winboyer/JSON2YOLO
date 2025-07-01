import os
import xml.etree.ElementTree as ET

def get_all_xml_files(folder_path):
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.xml')]

if __name__ == "__main__":
    folder = "/home/jinyfeng/datas/ai-construction/SODA/VOC2007/Annotations"  # 可以修改为你的文件夹路径
    xml_files = get_all_xml_files(folder)
    class_count = {}

    print(len(xml_files), "XML files found.")
    for idx, xml_file in enumerate(xml_files):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for obj in root.findall('object'):
            name = obj.find('name')
            if name is not None:
                class_name = name.text
                if class_name in class_count:
                    class_count[class_name] += 1
                else:
                    class_count[class_name] = 1

    print("类别统计：")
    for class_name, count in class_count.items():
        print(f"{class_name}: {count}")


