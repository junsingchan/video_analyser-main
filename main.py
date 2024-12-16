import asyncio
import os
from dotenv import load_dotenv
from video_analyser import analyse_video
from spider import download_video

load_dotenv()
API_KEY = os.getenv("KEY")


def download_and_analyse_video(url, csv_path, transcript_path, api_key):
    video_path = download_video(url)
    asyncio.run(
        analyse_video(
            video_path,
            csv_path=csv_path,
            transcript_path=transcript_path,
            api_key=api_key,
        )
    )
    os.remove(video_path)
    return csv_path, transcript_path


if __name__ == "__main__":
    asyncio.run(
        analyse_video(
            video_path="test/test.mp4",
            csv_path="results/test.csv",
            transcript_path="results/test.txt",
            api_key=API_KEY,
        )
    )
