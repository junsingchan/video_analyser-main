import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import Request

load_dotenv()
API_KEY = os.getenv("KEY")


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
    api_key: str = API_KEY
    base_url: str = "https://api.bltcy.ai/v1"
    min_scene_duration_seconds: Optional[float] = 3.0
    max_duration_seconds: Optional[int] = 300
    debug: Optional[bool] = True
