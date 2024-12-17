import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from spider import download_video
from video_analyser import analyse_video


app = FastAPI()


class VideoAnalysisRequest(BaseModel):
    video_path: str
    csv_path: str
    transcript_path: str
    api_key: str
    base_url: str = "https://api.bltcy.ai/v1"
    min_scene_duration_seconds: Optional[float] = 3.0
    max_duration_seconds: Optional[int] = 300
    debug: Optional[bool] = True


class DownloadAndAnalyseRequest(BaseModel):
    url: str
    csv_path: str
    transcript_path: str
    api_key: str


@app.post("/analyse-video")
async def analyse_video_endpoint(request: VideoAnalysisRequest):
    try:
        csv_path, transcript_path = await analyse_video(
            video_path=request.video_path,
            csv_path=request.csv_path,
            transcript_path=request.transcript_path,
            api_key=request.api_key,
            base_url=request.base_url,
            min_scene_duration_seconds=request.min_scene_duration_seconds,
            max_duration_seconds=request.max_duration_seconds,
            debug=request.debug,
        )
        return {"csv_path": csv_path, "transcript_path": transcript_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/download-and-analyse")
def download_and_analyse(request: DownloadAndAnalyseRequest):
    try:
        csv_path, transcript_path = download_and_analyse_video(
            url=request.url,
            csv_path=request.csv_path,
            transcript_path=request.transcript_path,
            api_key=request.api_key,
        )
        return {"csv_path": csv_path, "transcript_path": transcript_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
