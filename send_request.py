import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("KEY")

def send_request(data):
    url = "http://vanalyser.hgwl633.com:6688/download-and-analyse"
    response = requests.post(url, json=data)
    print(response)
    result = response.json()
    return result


url = "8.94 V@l.pD 10/04 teb:/ ChatGPT实时视频通话功能实测 对事物的辨别能力惊人  https://v.douyin.com/iUmYDHqP/ 复制此链接，打开Dou音搜索，直接观看视频！"
data = {"url": url, "api_key": API_KEY}
result = send_request(data)
print(result)  # 输出：{"result": "processed: test_data"}
