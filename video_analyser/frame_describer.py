import asyncio
import base64
from typing import List
import aiohttp
from loguru import logger
from openai import OpenAI


class FrameDescriber:
    def __init__(self, api_key=None, base_url="https://api.bltcy.ai/v1", debug=False):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.debug = debug

    async def describe_image(
        self,
        image_path,
        prompt="这是短视频的一个分镜。请先描述画面，然后从短视频拍摄技巧角度分析这个分镜。字数在80字以内。",
        model="gpt-4o-mini",
        max_tokens=200,
        detail="low",
    ):
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": detail,
                                },
                            },
                        ],
                    }
                ],
                max_tokens=max_tokens,
            ),
        )

        if self.debug:
            logger.debug(response.choices[0].message.content)
        return response.choices[0].message.content

    async def describe_images_concurrent(
        self, frames: List[str], max_concurrent: int = 5
    ) -> List[str]:
        async with aiohttp.ClientSession():
            # 将frames分成大小为max_concurrent的批次
            results = []
            for i in range(0, len(frames), max_concurrent):
                batch = frames[i : i + max_concurrent]
                # 为每个批次创建任务
                tasks = [self.describe_image(frame) for frame in batch]
                # 并发执行批次中的任务
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
            return results
