import asyncio
import os
import shutil
import time
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
    """
    分析视频主函数
    异步分析视频，处理分镜检测、转录和描述。

    参数:
        video_path (str): 视频文件路径。
        csv_path (str): CSV文件路径。
        transcript_path (str): 转录文件路径。
        api_key (str): API密钥。
        base_url (str): API基础URL。
        min_scene_duration_seconds (float): 最小分镜持续时间（秒）。
        max_duration_seconds (int): 最大视频时长（秒）。
        max_concurrent (int): 最大并发描述任务数。
        debug (bool): 是否启用调试模式。

    返回:
        tuple | None: 返回CSV和转录文件路径，或在出错时返回None。
    """
    start_time = time.time()
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    if not check_ffmpeg():
        return

    if not check_video_duration(video_path, max_duration_seconds):
        return

    scene_detector = SceneDetector(video_path, debug)
    recognizer_task = asyncio.create_task(init_recognizer(debug=debug))
    scene_detect_task = asyncio.create_task(
        asyncio.to_thread(
            scene_detector.detect_scenes,
            threshold=2.0,
            min_scene_duration=min_scene_duration_seconds,
            window_size=5,
            csv_path=csv_path,
            save_frames=True,
            frames_dir=temp_dir,
        )
    )

    # 第一步：检测分镜
    recognizer, _ = await asyncio.gather(recognizer_task, scene_detect_task)

    # 第二步：写入csv文案列
    transcript, temp_srt = transcribe(recognizer, video_path)
    save_transcript(transcript_path, transcript)
    subs = pysrt.open(temp_srt)
    rows = read_csv_rows(csv_path)
    scene_times = calculate_scene_times(rows)
    scene_transcripts = organize_subtitles_by_scene(subs, scene_times)
    scripts = prepare_script_values(scene_transcripts)
    header, rows = update_csv_column(csv_path, "文案", scripts)
    save_csv(csv_path, header, rows)

    # 第三步: 写入csv描述列
    frame_describer = FrameDescriber(api_key, base_url, debug)
    frames_description = await frame_describer.describe_images_concurrent(
        scene_detector.saved_frames, max_concurrent
    )
    header, rows = update_csv_column(csv_path, "描述", frames_description)
    save_csv(csv_path, header, rows)

    shutil.rmtree(temp_dir)
    duration = time.time() - start_time
    logger.info(f"视频分析完成！用时：{duration:.2f}秒")
    return csv_path, transcript_path
