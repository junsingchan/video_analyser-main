import re
import requests
from .utils import HEADERS


def get_pipix_info(url):
    response = requests.get(url, headers=HEADERS)
    id_url = response.url
    item_id = re.search(r"/item/(.*?)\?app_id", id_url)[1]
    url_data = requests.get(
        f"http://h5.pipix.com/bds/webapi/item/detail/?item_id={item_id}"
    ).json()
    new_url = url_data["data"]["item"]["origin_video_download"]["url_list"][0]["url"]
    title = url_data["data"]["item"]["share"]["title"]
    img = url_data["data"]["item"]["video"]["video_download"]["cover_image"][
        "url_list"
    ][0]["url"]
    return {"url": new_url, "cover": img, "title": title, "type": "pipix"}
