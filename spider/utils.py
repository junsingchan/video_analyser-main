import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
}
DOUYIN_MOBILE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Referer": "https://www.douyin.com/?is_from_mobile_home=1&recommend=1",
}


def get_redirected_url(url):
    response = requests.get(
        url,
        headers=HEADERS,
        allow_redirects=False,
    )
    return response.headers.get("Location", url)


def extract_douyin_video_id(url):
    if url.isdigit():
        return url
    video_url = re.search(r"https?://[^\s]+", url)[0]
    redirected_url = get_redirected_url(video_url)
    return re.search(r"\d+", redirected_url)[0]
