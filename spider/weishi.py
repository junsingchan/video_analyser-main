import re
import requests
from .utils import HEADERS


def get_weishi_info(url):
    feed_id = re.search(r"feed\/(.*?)\/", url)[1]
    response = requests.get(
        f"https://h5.weishi.qq.com/webapp/json/weishi/WSH5GetPlayPage?feedid={feed_id}",
        headers=HEADERS,
    )
    data = response.json()["data"]["feeds"][0]
    new_url = data["video_url"]
    cover = data["images"][0]["url"]
    title = data["feed_desc"] if data["feed_desc"] else "速来围观有趣的视频"
    return {"url": new_url, "cover": cover, "title": title, "type": "weishi"}
