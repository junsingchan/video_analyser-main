import time
import subprocess
import sherpa_onnx
import numpy as np
from loguru import logger
from tempfile import NamedTemporaryFile
from .utils import Segment, correct_srt_with_transcript


def init_recognizer(
    model="weights/asr/sensevoice.onnx", tokens="weights/asr/tokens.txt", debug=False
):
    start_time = time.time()
    if debug:
        logger.debug(f"加载Sensevoice模型：{model}")

    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=model,
        tokens=tokens,
        use_itn=True,
        debug=False,
        num_threads=8,
        language="auto",
    )

    if debug:
        logger.debug(f"SenseVoice初始化用时：{time.time() - start_time:.2f}秒")
    return recognizer


def create_ffmpeg_command(
    audio_path, sample_rate=16000, format="f32le", codec="pcm_f32le"
):
    """创建通用的FFmpeg命令"""
    return [
        "ffmpeg",
        "-i",
        audio_path,
        "-f",
        format,
        "-acodec",
        codec,
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "pipe:1",
    ]


def load_audio(
    audio_path, sample_rate=16000, format="f32le", codec="pcm_f32le", dtype=np.float32
):
    """通用音频加载函数"""
    command = create_ffmpeg_command(audio_path, sample_rate, format, codec)
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        audio_data, _ = process.communicate()
        samples = np.frombuffer(audio_data, dtype=dtype)
        if dtype == np.int16:
            samples = samples.astype(np.float32) / 32768
        return samples, sample_rate
    except Exception as e:
        raise RuntimeError(f"音频加载失败: {str(e)}")


def transcribe_sensevoice(audio, recognizer, debug=False):
    """音频转录为文本"""
    start_time = time.time()
    audio, sample_rate = load_audio(audio)
    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, audio)
    recognizer.decode_stream(stream)
    result_text = stream.result.text
    duration = time.time() - start_time

    word_count = len(result_text)
    logger.debug(
        f"转录用时：{duration:.2f}秒，字数：{word_count}（{duration * 1000 / word_count:.2f}毫秒/字）"
    ) if word_count > 0 and debug else logger.debug(
        f"转录用时：{duration:.2f}秒，无结果"
    )
    return result_text


def generate_subtitles(
    sound_file,
    recognizer,
    silero_vad_model,
    sample_rate=16000,
    srt_path="subtitle.srt",
    debug=False,
):
    audio, _ = load_audio(
        sound_file,
        sample_rate=sample_rate,
        format="s16le",
        codec="pcm_s16le",
        dtype=np.int16,
    )

    frames_per_read = int(sample_rate * 100)  # 100 second

    recognizer.create_stream()
    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = silero_vad_model
    config.silero_vad.threshold = 0.2
    config.silero_vad.min_silence_duration = 0.15
    config.silero_vad.min_speech_duration = 0.05
    config.silero_vad.max_speech_duration = 5
    config.sample_rate = sample_rate

    window_size = config.silero_vad.window_size

    buffer = []
    vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=100)

    segment_list = []

    if debug:
        logger.debug("生成字幕中...")
    start_time = time.time()

    # 处理音频数据
    for i in range(0, len(audio), frames_per_read):
        samples = audio[i : i + frames_per_read]
        if len(samples) == 0:
            break

        buffer = np.concatenate([buffer, samples])
        while len(buffer) > window_size:
            vad.accept_waveform(buffer[:window_size])
            buffer = buffer[window_size:]

    vad.flush()

    # VAD处理和识别部分
    while not vad.empty():
        segment = Segment(
            start=vad.front.start / sample_rate,
            duration=len(vad.front.samples) / sample_rate,
        )

        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, vad.front.samples)
        recognizer.decode_stream(stream)

        segment.text = stream.result.text
        segment_list.append(segment)

        vad.pop()

    # 写入SRT文件
    with open(srt_path, "w", encoding="utf-8") as f:
        counter = 1
        for seg in segment_list:
            split_segments = seg.split_by_punctuation()
            for split_seg in split_segments:
                print(counter, file=f)
                print(split_seg, file=f)
                print("", file=f)
                counter += 1

    if debug:
        duration = len(audio) / sample_rate
        elapsed_seconds = time.time() - start_time
        logger.debug(
            f"字幕生成成功：{srt_path}（{elapsed_seconds:.2f}秒，音频时长：{duration:.2f}秒）"
        )


def transcribe(video_path: str, srt_path: str = None) -> tuple:
    # 初始化识别器
    recognizer = init_recognizer(
        model="weights/asr/sensevoice.onnx", tokens="weights/asr/tokens.txt", debug=True
    )

    srt_path = (
        NamedTemporaryFile(suffix=".srt", dir="temp").name
        if srt_path is None
        else srt_path
    )
    generate_subtitles(
        recognizer=recognizer,
        sound_file=video_path,
        silero_vad_model="weights/asr/silero_vad.onnx",
        srt_path=srt_path,
    )

    # 转录文本
    transcript = transcribe_sensevoice(
        audio=video_path, recognizer=recognizer, debug=True
    )

    # 校对SRT文件内容
    corrected_srt = correct_srt_with_transcript(srt_path, transcript)

    # 将校对后的内容写回文件
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(corrected_srt)

    return transcript, srt_path
