import os
import requests
from datetime import datetime
from datetime import timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
import re

def convert_date_to_timestamp(date_str):
    """
    Convert a date string to a timestamp.

    :param date_str: The date string in the format 'YYYY-MM-DDTHH:MM:SSZ'.
    :return: The corresponding timestamp.
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return str(int(dt.timestamp()))
    except ValueError as e:
        print(f"Invalid date format: {e}")
        return None

def fetch_data_from_http_service(url, device_name, start_time, end_time):
    """
    Fetch data from an HTTP service using the provided parameters.

    :param url: The endpoint URL of the HTTP service.
    :param device_name: The name of the device to query.
    :param start_time: The start time for the query (e.g., '2023-01-01T00:00:00Z').
    :param end_time: The end time for the query (e.g., '2023-01-02T00:00:00Z').
    :return: The response data from the HTTP service.
    """
    headers = {'Content-Type': 'application/json'}
    payload = {
        "deviceName": device_name,
        "start_time": start_time,
        "end_time": end_time
    }
    print(type(payload))
    print(payload)
    try:
        response = requests.get(url, params=payload, headers=headers)
        print(response.status_code)
        # print(response.json())
        # print(response.encoding)
        # print(response.url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def download_imgs(url, device_names, start_time, end_time):
    """
    Download images from the specified URL for a given device and time range.

    :param url: The endpoint URL of the HTTP service.
    :param device_name: The name of the device to query.
    :param start_time: The start time for the query (e.g., '2023-01-01T00:00:00Z').
    :param end_time: The end time for the query (e.g., '2023-01-02T00:00:00Z').
    """
    start_timestamp = convert_date_to_timestamp(start_time)
    end_timestamp = convert_date_to_timestamp(end_time)
    if start_timestamp and end_timestamp:
        print(f"Start timestamp: {start_timestamp}")
        print(f"End timestamp: {end_timestamp}")

    time_date = start_time[:10].replace("-", "")
    os.makedirs(time_date, exist_ok=True)
    # 10号电梯（KRIPCH_122203166_28），9号电梯（KRIPCH_108226008_43）
    total_count = 0
    
    for device_name in device_names:
        data = fetch_data_from_http_service(url, device_name, start_timestamp, end_timestamp)
        if data:
            print("Data fetched successfully:")
            print(data.keys())
            dict_data = data['data']
            print(len(dict_data))
            total_count += len(dict_data)
            # 将数据写入本地 txt 文件
            # 动态生成文件名
            url_txtfile_name = f"image_data_{time_date}.txt"
            try:
                with open(url_txtfile_name, "w", encoding="utf-8") as txtfile:
                    for idx, item in enumerate(dict_data):
                        # 将每个数据项转换为字符串并写入文件
                        # print(item.keys())
                        image_url = item['pic']
                        print(image_url)
                        # txtfile.write(image_url + "\n")
                        try:
                            response = requests.get(image_url)
                            response.raise_for_status()  # 检查请求是否成功
                            # image_file_name = f"{file_prefix}_image_{idx + 1}.jpg"  # 动态生成图片文件名
                            # image_file_name = f"image_{idx + 1}.jpg"  # 动态生成图片文件名
                            # Extract the file name from the image URL
                            image_file_name = image_url.split("/")[-1]
                            image_file_path = os.path.join(time_date, image_file_name)
                            with open(image_file_path, "wb") as img_file:
                                img_file.write(response.content)  # 保存图片内容
                            print(f"Image {idx + 1} has been downloaded: {image_file_name}")
                        except requests.exceptions.RequestException as e:
                            print(f"Failed to download image {idx + 1} from {image_url}: {e}")
                # print(f"Image URLs have been written to {url_txtfile_name}")
            except IOError as e:
                print(f"Failed to write data to file: {e}")
        else:
            print("Failed to fetch data.")

    print(f"Total count of images: {total_count}")
    print("All images have been downloaded.")


# Example usage
if __name__ == "__main__":
    
    scheduler = BlockingScheduler()

    url = "http://iot.krzhibo.com/admin/common/cloudData/getResourceAll"
    device_names = ["KRIPCH_108226008_43", "KRIPCH_122203166_28"]
    # 获取当前目录下的文件夹
    folders = [name for name in os.listdir('.') if os.path.isdir(name)]
    # 过滤出符合 yyyymmdd 格式的文件夹
    date_pattern = re.compile(r'^\d{8}$')
    date_folders = [f for f in folders if date_pattern.match(f)]
    # 获取离当前最近的日期
    today = datetime.now()
    closest_folder = None
    min_diff = None
    for folder in date_folders:
        try:
            folder_date = datetime.strptime(folder, "%Y%m%d")
            diff = abs((folder_date - today).days)
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_folder = folder
        except ValueError:
            continue
    print(f"Closest date folder: {closest_folder}")
    # 获取 closest_folder+1 的日期并格式化
    if closest_folder:
        try:
            folder_date_obj = datetime.strptime(closest_folder, "%Y%m%d")
            next_day_obj = folder_date_obj + timedelta(days=1)
            formatted_next_day = next_day_obj.strftime("%Y-%m-%dT00:00:00Z")
            print(f"Formatted next day: {formatted_next_day}")
        except Exception as e:
            print(f"Error formatting next day: {e}")
    else:
        formatted_next_day = None
    print(formatted_next_day)

    current_date_str = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
    print(f"Current date in required format: {current_date_str}")


    start_time = "2025-12-15T00:00:00Z"
    end_time = "2025-12-17T00:00:00Z"
    # 判断 start_time 和 end_time 相差几天
    dt_start = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    dt_end = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
    delta_days = (dt_end - dt_start).days
    print(f"Start time and end time are {delta_days} day(s) apart.")
    if delta_days < 0:
        print("Error: Start time must be earlier than end time.")
        exit(1) 
    elif delta_days >= 1:
        for idx in range(delta_days):
            current_start_time = (dt_start + timedelta(days=idx)).strftime("%Y-%m-%dT00:00:00Z")
            current_end_time = (dt_start + timedelta(days=idx + 1)).strftime("%Y-%m-%dT00:00:00Z")
            print(f"Downloading images for {current_start_time} to {current_end_time}")
            download_imgs(url, device_names, current_start_time, current_end_time)



            # 每周一上午9点定时执行
            # 可以使用 Windows 任务计划程序或 Linux 的 cron 来定时运行本脚本
            # 例如，Linux 下可添加如下 cron 任务（假设 Python 路径和脚本路径已配置好）：
            # 0 9 * * 1 /usr/bin/python3 /f:/jinyfeng/projects/JSON2YOLO/img_downloads.py

            # 或者用 APScheduler 在代码内实现定时（需安装 apscheduler）
            # from apscheduler.schedulers.blocking import BlockingScheduler
            # scheduler = BlockingScheduler()
            # scheduler.add_job(main, 'cron', day_of_week='mon', hour=9, minute=0)
            # scheduler.start()