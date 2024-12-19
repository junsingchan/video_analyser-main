import os
from tempfile import NamedTemporaryFile
from fastapi import FastAPI, HTTPException
import uvicorn
from api_models import VideoAnalysisRequest, DownloadAndAnalyseRequest
from api_utils import convert_to_json_data
from spider import download_video
from video_analyser import analyse_video

app = FastAPI()


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
        json_result = convert_to_json_data(csv_path, transcript_path)
        return json_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download-and-analyse")
async def download_and_analyse_endpoint(request: DownloadAndAnalyseRequest):
    try:
        video_path, video_id = download_video(request.url)
        temp_csv = NamedTemporaryFile(suffix=".csv", dir="temp").name
        temp_txt = NamedTemporaryFile(suffix=".txt", dir="temp").name
        await analyse_video(
            video_path,
            csv_path=temp_csv,
            transcript_path=temp_txt,
            api_key=request.api_key,
            base_url=request.base_url,
            min_scene_duration_seconds=request.min_scene_duration_seconds,
            max_duration_seconds=request.max_duration_seconds,
            debug=request.debug,
        )
        json_result = convert_to_json_data(temp_csv, temp_txt, video_id)
        for file in [video_path, temp_csv, temp_txt]:
            if os.path.exists(file):
                os.remove(file)
        return json_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
