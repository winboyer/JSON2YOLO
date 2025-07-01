import os
import requests
from datetime import datetime

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

# Example usage
if __name__ == "__main__":
    url = "http://iot.krzhibo.com/admin/common/cloudData/getResourceAll"
    
    start_time = "2025-06-19T00:00:00Z"
    end_time = "2025-06-20T00:00:00Z"
    start_timestamp = convert_date_to_timestamp(start_time)
    end_timestamp = convert_date_to_timestamp(end_time)
    if start_timestamp and end_timestamp:
        print(f"Start timestamp: {start_timestamp}")
        print(f"End timestamp: {end_timestamp}")

    time_date = start_time[:10].replace("-", "")
    os.makedirs(time_date, exist_ok=True)
    # 10号电梯（KRIPCH_122203166_28），9号电梯（KRIPCH_108226008_43）
    device_names = ["KRIPCH_108226008_43", "KRIPCH_122203166_28"]
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
                        txtfile.write(image_url + "\n")
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
                print(f"Image URLs have been written to {url_txtfile_name}")
            except IOError as e:
                print(f"Failed to write data to file: {e}")
        else:
            print("Failed to fetch data.")

    print(f"Total count of images: {total_count}")
    print("All images have been downloaded.")

