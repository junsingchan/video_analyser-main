import json
import re
import requests


def get_kuaishou_info(url):
    matches = re.findall(
        r"(http|https)://([\w\d\-_]+[\.\w\d\-_]+)[:\d+]?([\/]?[\w\/\.]+)", url
    )
    url = matches[0][0]
    response = requests.get(url, headers={"Referer": "https://v.kuaishou.com"})
    video_data = json.loads(
        response.text.split("window.pageData=")[1].split("</script>")[0]
    )["video"]
    return {
        "url": video_data["srcNoMark"],
        "cover": video_data["poster"],
        "title": video_data["caption"],
        "type": "kuaishou",
    }
