import asyncio
import os
import shutil
import time
from typing import List
import aiohttp
import pysrt
from loguru import logger
from .scene_detector import SceneDetector
from .frame_describer import FrameDescriber
from .transcriber import transcribe, init_recognizer
from .utils import (
    save_csv,
    check_video_duration,
    update_csv_column,
    read_csv_rows,
    save_transcript,
    prepare_script_values,
    calculate_scene_times,
    organize_subtitles_by_scene,
    check_ffmpeg,
)


def update_csv_scripts(
    regconizer, csv_path: str, transcript_path: str, video_path: str
) -> tuple:
    """在CSV文件中添加文案列内容"""
    transcript, temp_srt = transcribe(regconizer, video_path)
    save_transcript(transcript_path, transcript)
    subs = pysrt.open(temp_srt)
    rows = read_csv_rows(csv_path)
    scene_times = calculate_scene_times(rows)
    scene_transcripts = organize_subtitles_by_scene(subs, scene_times)
    scripts = prepare_script_values(scene_transcripts)
    return update_csv_column(csv_path, "文案", scripts)


async def describe_image_async(frame_path: str, frame_describer) -> str:
    return await frame_describer.describe_image_async(frame_path)


async def describe_images_concurrent(
    frame_describer, frames: List[str], max_concurrent: int = 5
) -> List[str]:
    async with aiohttp.ClientSession():
        # 将frames分成大小为max_concurrent的批次
        batch_size = max_concurrent
        results = []

        for i in range(0, len(frames), batch_size):
            batch = frames[i : i + batch_size]
            # 为每个批次创建任务
            tasks = [describe_image_async(frame, frame_describer) for frame in batch]
            # 并发执行批次中的任务
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        return results


async def analyse_video(
    video_path: str,
    csv_path: str,
    transcript_path: str,
    api_key: str,
    base_url: str = "https://api.bltcy.ai/v1",
    min_scene_duration_seconds: float = 3.0,
    max_duration_seconds: int = 300,
    max_concurrent: int = 8,
    debug: bool = True,
) -> tuple | None:
    start_time = time.time()
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    if not check_ffmpeg():
        return

    if not check_video_duration(video_path, max_duration_seconds):
        return

    # 启动recognizer初始化任务
    recognizer_task = asyncio.create_task(init_recognizer(debug=debug))

    # 第一步：检测分镜
    scene_detector = SceneDetector(video_path, debug)
    scene_detector.detect_scenes(
        min_scene_duration=min_scene_duration_seconds,
        csv_path=csv_path,
        frames_dir=temp_dir,
    )

    # 第二步：等待recognizer初始化完成并写入csv文案列
    recognizer = await recognizer_task
    header, rows = update_csv_scripts(recognizer, csv_path, transcript_path, video_path)
    save_csv(csv_path, header, rows)

    # 第三步: 写入csv描述列
    frame_describer = FrameDescriber(api_key, base_url, debug)
    frames_description = await describe_images_concurrent(
        frame_describer, scene_detector.saved_frames, max_concurrent
    )
    header, rows = update_csv_column(csv_path, "描述", frames_description)
    save_csv(csv_path, header, rows)

    shutil.rmtree(temp_dir)
    duration = time.time() - start_time
    logger.info(f"视频分析完成！用时：{duration:.2f}秒")
    return csv_path, transcript_path
