import asyncio
import os
from dotenv import load_dotenv

from utils import convert_to_json_data
from video_analyser import analyse_video
from spider import download_video

load_dotenv()
API_KEY = os.getenv("KEY")


def download_and_analyse_video(url, csv_path, transcript_path, api_key, delete_temp=True):
    video_path, video_id = download_video(url)
    asyncio.run(
        analyse_video(
            video_path,
            csv_path=csv_path,
            transcript_path=transcript_path,
            api_key=api_key,
        )
    )

    json_result = convert_to_json_data(csv_path, transcript_path, video_id)
    if delete_temp:
        os.remove(video_path)
        os.remove(csv_path)
        os.remove(transcript_path)

    return json_result


if __name__ == "__main__":
    csv_path, transcript_path = asyncio.run(analyse_video(
        video_path="test/test.mp4",
        csv_path="results/test.csv",
        transcript_path="results/test.txt",
        api_key=API_KEY,
        debug=True,
    ))
    json_result = convert_to_json_data(csv_path, transcript_path)
    print(json_result)