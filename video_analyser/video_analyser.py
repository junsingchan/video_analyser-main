import os
import shutil
import time
import pysrt
from loguru import logger
from .scene_detector import SceneDetector
from .frame_describer import FrameDescriber
from .transcriber import transcribe
from .utils import (
    save_csv,
    check_video_duration,
    update_csv_column,
    read_csv_rows,
    save_transcript,
    prepare_script_values,
    calculate_scene_times,
    organize_subtitles_by_scene,
)


def update_csv_scripts(csv_path: str, transcript_path: str, video_path: str) -> tuple:
    """在CSV文件中添加文案列内容"""
    transcript, temp_srt = transcribe(video_path)
    save_transcript(transcript_path, transcript)
    subs = pysrt.open(temp_srt)
    rows = read_csv_rows(csv_path)
    scene_times = calculate_scene_times(rows)
    scene_transcripts = organize_subtitles_by_scene(subs, scene_times)
    scripts = prepare_script_values(scene_transcripts)
    return update_csv_column(csv_path, "文案", scripts)


def analyse_video(
    video_path: str,
    csv_path: str,
    transcript_path: str,
    api_key: str,
    base_url: str = "https://api.bltcy.ai/v1",
    min_scene_duration_seconds: float = 3.0,
    max_duration_seconds: int = 300,
    debug: bool = True,
) -> tuple:
    start_time = time.time()
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    if not check_video_duration(video_path, max_duration_seconds):
        return

    # 第一步：检测分镜
    scene_detector = SceneDetector(video_path, debug)
    scene_detector.detect_scenes(
        min_scene_duration=min_scene_duration_seconds,
        csv_path=csv_path,
        frames_dir=temp_dir,
    )

    # 第二步：写入csv文案列
    header, rows = update_csv_scripts(csv_path, transcript_path, video_path)
    save_csv(csv_path, header, rows)

    # 第三步: 写入csv描述列
    frame_describer = FrameDescriber(api_key, base_url, debug)
    frames_description = []
    for frame_to_describe in scene_detector.saved_frames:
        description = frame_describer.describe_image(frame_to_describe)
        frames_description.append(description)
    header, rows = update_csv_column(csv_path, "描述", frames_description)
    save_csv(csv_path, header, rows)

    shutil.rmtree(temp_dir)
    duration = time.time() - start_time
    logger.info(f"视频分析完成！用时：{duration:.2f}秒")
    return csv_path, transcript_path
