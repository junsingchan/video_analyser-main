import asyncio
import os
from dotenv import load_dotenv
from video_analyser import analyse_video

load_dotenv()
API_KEY = os.getenv("KEY")

if __name__ == "__main__":
    asyncio.run(
        analyse_video(
            video_path="test/test.mp4",
            csv_path="results/test.csv",
            transcript_path="results/test.txt",
            api_key=API_KEY,
        )
    )
