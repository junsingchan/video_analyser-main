import csv


def convert_to_json_data(csv_path, transcript_path, video_id=None):
    # 读取CSV文件
    scenes = []
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            scene = {
                "scene_number": row["分镜"],
                "duration": float(row["时长（秒）"]),
                "text": row["文案"],
                "description": row.get("描述", ""),
            }
            scenes.append(scene)

    # 读取transcript文件
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # 构建最终的JSON结构
    result = {"video_id": video_id, "scenes": scenes, "transcript": transcript}

    return result
