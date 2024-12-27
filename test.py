from spider import download_video


if __name__ == "__main__":
    video_path, video_id = download_video(
        "https://www.douyin.com/video/7401060142978043177", save_path="temp/xxx.mp4"
    )
