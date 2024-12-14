from loguru import logger
import cv2
import csv
from tqdm import tqdm
import os
from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class VideoFeatures:
    hist: np.ndarray
    edge_hist: np.ndarray


class SceneDetector:
    def __init__(self, video_path: str, debug: bool = True):
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.saved_frames = []
        self.debug = debug

    @staticmethod
    def calculate_features(frame: np.ndarray) -> VideoFeatures:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        edges = cv2.Canny(gray, 100, 200)
        edge_hist = cv2.calcHist([edges], [0], None, [256], [0, 256])

        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(edge_hist, edge_hist, 0, 1, cv2.NORM_MINMAX)

        return VideoFeatures(hist, edge_hist)

    @staticmethod
    def compare_features(prev: VideoFeatures, curr: VideoFeatures) -> float:
        hist_diff = cv2.compareHist(prev.hist, curr.hist, cv2.HISTCMP_BHATTACHARYYA)
        edge_diff = cv2.compareHist(
            prev.edge_hist, curr.edge_hist, cv2.HISTCMP_BHATTACHARYYA
        )
        return 0.7 * hist_diff + 0.3 * edge_diff

    def detect_scenes(
        self,
        threshold: float = 2.0,
        min_scene_duration: float = 1.0,
        window_size: int = 5,
        csv_path: str = "scene_detection.csv",
        save_frames: bool = True,
        frames_dir: str = "scene_frames",
    ) -> List[int]:
        os.makedirs(frames_dir, exist_ok=True)

        min_frames = int(min_scene_duration * self.fps)
        scene_changes = [0]
        diff_buffer = []
        prev_features = None

        if save_frames:
            self._save_frame(0, frames_dir)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        with tqdm(total=self.total_frames, desc="检测分镜") as pbar:
            for frame_num in range(self.total_frames):
                ret, frame = self.cap.read()
                if not ret:
                    break

                curr_features = self.calculate_features(frame)
                if prev_features:
                    diff = self.compare_features(prev_features, curr_features)
                    diff_buffer.append(diff)
                    diff_buffer = diff_buffer[-window_size:]

                    if len(diff_buffer) == window_size:
                        avg_diff = sum(diff_buffer) / window_size
                        if (
                            avg_diff > threshold / 100.0
                            and (frame_num - scene_changes[-1]) >= min_frames
                        ):
                            scene_changes.append(frame_num)
                            if self.debug:
                                logger.debug(
                                    f"检测到分镜：第{frame_num}帧，差异值：{avg_diff:.4f}"
                                )
                            if save_frames:
                                self._save_frame(frame_num, frames_dir)

                prev_features = curr_features
                pbar.update(1)

        scene_changes = self._finalize_scenes(scene_changes)
        self._write_csv(scene_changes, csv_path)

        if self.debug:
            logger.debug(f"分镜数：{len(scene_changes) - 1}")
            logger.debug(f"分镜点：{scene_changes[:-1]}")

        return scene_changes[:-1]

    def _save_frame(self, frame_num: int, output_dir: str) -> None:
        ret, frame = self.cap.read()
        if ret:
            saved_frame_name = os.path.join(output_dir, f"frame_{frame_num}.jpg")
            cv2.imwrite(saved_frame_name, frame)
            self.saved_frames.append(saved_frame_name)

    def _finalize_scenes(self, scene_changes: List[int]) -> List[int]:
        if self.total_frames - scene_changes[-1] <= 3:
            scene_changes.pop()
        scene_changes.append(self.total_frames)
        return self._merge_close_scenes(scene_changes, int(self.fps * 0.5))

    @staticmethod
    def _merge_close_scenes(scene_changes: List[int], min_gap: int) -> List[int]:
        if len(scene_changes) <= 2:
            return scene_changes

        merged = [scene_changes[0]]
        for change in scene_changes[1:-1]:
            if change - merged[-1] >= min_gap:
                merged.append(change)
        merged.append(scene_changes[-1])

        return merged

    def _write_csv(self, scene_changes: List[int], output_path: str) -> None:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["分镜", "时长（秒）"])

            for i in range(len(scene_changes) - 1):
                duration = round(
                    (scene_changes[i + 1] - scene_changes[i]) / self.fps, 2
                )
                writer.writerow([f"分镜 {i + 1}", duration, "", ""])
