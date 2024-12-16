import csv
import os.path
import shutil
import subprocess
from dataclasses import dataclass
from datetime import timedelta
import cv2
import pysrt
from difflib import SequenceMatcher
import re
from loguru import logger


def normalize_text(text: str) -> str:
    """规范化文本：处理空格和标点"""
    # 删除多余空格
    text = " ".join(text.split())

    # 确保中文标点前后没有空格 - 使用原始字符串(r)或双反斜杠
    text = re.sub(r'\s*([，。！？、；：“”"' "（）])\\s*", r"\1", text)

    # 处理省略号
    text = re.sub(r"\.{3,}", "...", text)

    # 处理句尾标点
    if text and not any(text.endswith(p) for p in ",，”。！？.!?"):
        text += "。"

    return text


def correct_srt_with_transcript(srt_path: str, transcript: str):
    """使用transcript校对srt文件内容"""
    # 读取SRT文件
    subs = pysrt.open(srt_path)

    # 对transcript分段并与srt字幕进行匹配校对
    corrected_content = []
    transcript_pos = 0

    for sub in subs:
        text = sub.text.strip()
        # 在transcript中查找最匹配的部分
        best_match = ""
        best_ratio = 0

        # 在transcript中搜索最佳匹配片段
        for i in range(
            max(0, transcript_pos - 50),
            min(len(transcript), transcript_pos + len(text) + 50),
        ):
            for j in range(i + len(text) // 2, min(len(transcript), i + len(text) * 2)):
                candidate = transcript[i:j]
                ratio = SequenceMatcher(None, text, candidate).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = candidate
                    transcript_pos = j

        # 如果找到较好的匹配(相似度>0.6)，使用transcript中的文本
        if best_ratio > 0.6:
            sub.text = best_match

        # 规范化文本格式
        sub.text = normalize_text(sub.text)
        corrected_content.append(str(sub))

    return "\n\n".join(corrected_content)


def save_csv(csv_path: str, header: list, rows: list):
    """保存更新后的CSV文件"""
    with open(csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def check_video_duration(video_path: str, max_duration_seconds: int = 300) -> bool:
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps

    video.release()

    if duration > max_duration_seconds:
        logger.error(
            f"视频时长({duration:.2f}秒)超过限制({max_duration_seconds}秒)，停止分析！"
        )
        return False

    return True


@dataclass
class Segment:
    start: float
    duration: float
    text: str = ""

    @property
    def end(self):
        return self.start + self.duration

    def split_by_punctuation(self):
        """根据标点符号切分文本,返回新的Segment列表"""
        # 定义标点符号
        puncts = ["。", "！", "？", "!", "?", "；", ";", "，"]

        # 如果文本为空或没有标点,直接返回当前segment
        if not self.text or not any(p in self.text for p in puncts):
            return [self]

        # 根据位置切分时间和文本
        segments = []
        last_pos = 0
        text_len = len(self.text)

        for i, char in enumerate(self.text):
            if char in puncts:
                if last_pos == i:
                    continue

                # 计算该部分文本占总时长的比例
                ratio = (i - last_pos + 1) / text_len
                duration = self.duration * ratio

                # 创建新的segment
                new_seg = Segment(
                    start=self.start + (self.duration * last_pos / text_len),
                    duration=duration,
                    text=self.text[last_pos : i + 1],
                )
                segments.append(new_seg)
                last_pos = i + 1

        # 处理最后一段文本
        if last_pos < text_len:
            ratio = (text_len - last_pos) / text_len
            new_seg = Segment(
                start=self.start + (self.duration * last_pos / text_len),
                duration=self.duration * ratio,
                text=self.text[last_pos:],
            )
            segments.append(new_seg)

        return segments

    def __str__(self):
        s = f"{timedelta(seconds=self.start)}"[:-3]
        s += " --> "
        s += f"{timedelta(seconds=self.end)}"[:-3]
        s = s.replace(".", ",")
        s += "\n"
        s += self.text
        return s


def update_csv_column(
    csv_path: str, column_name: str, values: list, empty_default: str = ""
) -> tuple:
    """CSV列更新函数"""
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)
        rows = list(reader)

    # 添加新列标题
    header.append(column_name)
    new_col_index = len(header) - 1

    # 为每行添加新列
    for i, row in enumerate(rows):
        row.append(empty_default)
        if i < len(values) and values[i]:
            row[new_col_index] = values[i]

    return header, rows


def read_csv_rows(csv_path: str) -> list:
    """读取CSV文件内容（跳过表头）"""
    with open(csv_path, "r", encoding="utf-8") as file:
        return list(csv.reader(file))[1:]


def save_transcript(transcript_path: str, transcript: str) -> None:
    """保存转写文本到文件"""
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)


def get_subtitle_start_seconds(sub: pysrt.SubRipItem) -> float:
    """计算字幕的开始时间（以秒为单位）"""
    return sub.start.seconds + sub.start.minutes * 60 + sub.start.hours * 3600


def prepare_script_values(scene_transcripts: list) -> list:
    """准备文案列的值"""
    return ["".join(transcripts) for transcripts in scene_transcripts]


def calculate_scene_times(rows: list) -> list:
    """计算每个分镜的时间范围"""
    scene_times = []
    current_time = 0
    for row in rows:
        end_time = current_time + float(row[1])
        scene_times.append((current_time, end_time))
        current_time = end_time
    return scene_times


def organize_subtitles_by_scene(subs: pysrt.SubRipFile, scene_times: list) -> list:
    """将字幕按分镜组织"""
    scene_transcripts = [[] for _ in range(len(scene_times))]
    for sub in subs:
        start_seconds = get_subtitle_start_seconds(sub)
        for scene_idx, (start_time, end_time) in enumerate(scene_times):
            if start_time <= start_seconds < end_time:
                scene_transcripts[scene_idx].append(sub.text)
                break
    return scene_transcripts


def check_ffmpeg():
    try:
        # 检查方法1: 使用shutil查找可执行文件
        check1 = shutil.which("ffmpeg") is not None

        # 检查方法2: 尝试执行ffmpeg命令
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            check2 = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            check2 = False

        # 检查方法3: 检查当前目录是否存在ffmpeg.exe
        check3 = os.path.exists("ffmpeg.exe")

        # 只要有一个检查通过就认为ffmpeg可用
        ffmpeg_available = check1 or check2 or check3

        if not ffmpeg_available:
            logger.error("FFmpeg未安装，无法进行分析！")
            return False

        return ffmpeg_available

    except Exception as e:
        logger.error(f"检查FFmpeg时发生错误: {str(e)}")
        return False
