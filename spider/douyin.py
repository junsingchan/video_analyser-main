import json
import re
import requests
from .utils import extract_douyin_video_id, DOUYIN_MOBILE_HEADERS


def get_douyin_info(url):
    video_id = extract_douyin_video_id(url)
    response = requests.get(
        f"https://www.iesdouyin.com/share/video/{video_id}/",
        headers=DOUYIN_MOBILE_HEADERS,
    )
    data = re.search(r"_ROUTER_DATA\s*=\s*(\{.*?\});", response.text)[1]
    json_data = json.loads(data)
    item_list = json_data["loaderData"]["video_(id)/page"]["videoInfoRes"]["item_list"][
        0
    ]
    title = item_list["desc"]
    video = item_list["video"]["play_addr"]["uri"]
    video_url = (
        f"https://www.douyin.com/aweme/v1/play/?video_id={video}"
        if "mp3" not in video
        else video
    )
    cover = item_list["video"]["cover"]["url_list"][0]
    return {"title": title, "cover": cover, "url": video_url, "type": "douyin"}
