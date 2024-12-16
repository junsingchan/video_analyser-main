import os
import time
import requests
from loguru import logger
from .utils import HEADERS
from .douyin import get_douyin_info
from .weishi import get_weishi_info
from .pipix import get_pipix_info
from .kuaishou import get_kuaishou_info


def get_video_info(url):
    if any(domain in url for domain in ["douyin", "aweme", "iesdouyin", "365yg"]):
        return get_douyin_info(url)
    elif "weishi" in url:
        return get_weishi_info(url)
    elif "pipix" in url:
        return get_pipix_info(url)
    elif any(domain in url for domain in ["chenzhongtech", "kuaishou"]):
        return get_kuaishou_info(url)
    else:
        return None


def download_video(url, save_path=None):
    start_time = time.time()
    video_info = get_video_info(url)
    video_url = video_info["url"]
    response = requests.get(video_url, headers=HEADERS, stream=True)

    if save_path is None:
        save_path = os.path.join(os.getcwd(), f"{video_info['title']}.mp4")
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)

    duration = time.time() - start_time
    size_mb = os.path.getsize(save_path) / 1024 / 1024
    logger.info(
        f"视频下载成功：{save_path}（耗时{duration:.2f}秒，大小{size_mb:.2f} MB）"
    )
    return save_path
