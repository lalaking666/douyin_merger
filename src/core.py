#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   core.py
@Time    :   2025/06/30 14:42:22
@Version :   1.0
"""


import json
import os
from pathlib import Path
from random import randint
from time import sleep
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from pydantic import BaseModel
import requests
from tqdm import tqdm
from xb import build_request_url_with_xb

# 从文本文件中读取cookie
with open(Path(__file__).parent / "cookies.json", "r") as f:
    COOKIES = {item["name"]: item["value"] for item in json.load(f)}

def load_config() -> Dict[str, Any]:
    """
    加载配置文件
    :return: 配置字典，包含users、ffmpeg_max_workers、store_dir等
    """
    config_file = Path(__file__).parent / "config.json"
    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_file}")
        return {"users": [], "ffmpeg_max_workers": 4, "store_dir": "data"}
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            return {
                "users": config.get("users", []),
                "ffmpeg_max_workers": config.get("ffmpeg_max_workers", 4),
                "store_dir": config.get("store_dir", "data")
            }
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {"users": [], "ffmpeg_max_workers": 4, "store_dir": "data"}


class DouyinUserInfo(BaseModel):
    uid: str
    sec_uid: str
    nick: str
    

class DouyinVideoInfo(BaseModel):
    vid: str
    desc: str
    create_time: int
    user: DouyinUserInfo
    video_links: List[str]
    local_file_path: Optional[Path] = None
    resize_video_path: Optional[Path] = None
    


class DouyinVideoSpider:
    COOKIES = COOKIES
    LIST_API = "https://www.douyin.com/aweme/v1/web/aweme/post/?device_platform=webapp&aid=6383&count=20&channel=channel_pc_web&sec_user_id={sec_uid}&max_cursor={cursor}&locate_item_id=7353326026929360163&locate_query=false&show_live_replay_strategy=1&need_time_list=0&time_list_query=0&whale_cut_token=&cut_version=1&count=10&publish_video_strategy_type=2&pc_client_type=1&version_code=290100&version_name=29.1.0&cookie_enabled=true&screen_width=1680&screen_height=945&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac+OS&os_version=10.15.7&cpu_core_num=6&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50&webid=7496388989713876490&msToken="
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    HEADERS = {
        "authority": "www.douyin.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "referer": "https://www.douyin.com/",
        "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": USER_AGENT,
    }

    def __init__(self, local_video_list: List[DouyinVideoInfo]=[]):
        # self.local_video_list = local_video_list
        self._vid_set = set([video.vid for video in local_video_list])


    # 获取视频列表
    def get_post_list(self, nick: str, sec_uid: str)->List[DouyinVideoInfo]:
        cursor = ""
        while True:
            url = self.LIST_API.format(sec_uid=sec_uid, cursor=cursor)
            url = build_request_url_with_xb(url, self.HEADERS["user-agent"])

            response = requests.get(url, headers=self.HEADERS, cookies=self.COOKIES)
            data = response.json()
            if data.get("aweme_list"):
                has_new = False # 是否有新的视频
                for item in data.get("aweme_list"):
                    if item.get("aweme_id") in self._vid_set:
                        logger.info(f"已下载视频,跳过: {item.get('aweme_id')}")
                        continue
                    # 过滤掉非video发文
                    if not item.get('video',{}).get('bit_rate'):
                        logger.info(f"非视频发文,跳过: {item.get('aweme_id')}, url: {item.get('share_url')}")
                        continue
                    
                    # 提取视频直链
                    e = sorted(item['video']['bit_rate'], key=lambda x: x['bit_rate'], reverse=True)[0]
                    video_links = e.get('play_addr').get('url_list')
                    
                    user = DouyinUserInfo(
                        uid=item.get("author").get("uid"),
                        sec_uid=item.get("author").get("sec_uid"),
                        nick=nick
                    )
                    logger.info(f"获取到视频: {item.get('aweme_id')}")
                    yield DouyinVideoInfo(
                        vid=item.get("aweme_id"),
                        desc=item.get("desc"),
                        create_time=item.get("create_time"),
                        user=user,
                        video_links = video_links
                    )
                    has_new = True
                if not has_new:
                    logger.info(f"没有新的视频了,结束")
                    break
                if data.get("has_more"):
                    cursor = data.get("max_cursor")
                    logger.info(f"有更多视频,继续获取: {cursor}")
                    sleep(randint(1,2))
                    continue
                else:
                    logger.info(f"没有更多视频了,结束")
                    break
            else:
                logger.info(f"没有更多视频了,结束")
                break
            

class DouyinMergerCore:
    def __init__(self, store_dir: str = "data"):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
    
    def download_video(self, video_info: DouyinVideoInfo)->bool:
        for video_link in video_info.video_links:
            response = requests.head(video_link, allow_redirects=False)
            if response.status_code == 403:
                continue
            elif response.status_code == 302:
                for i in range(5):
                    try:
                        response = requests.get(video_link, timeout=600)
                        break
                    except requests.exceptions.Timeout:
                        logger.error(f"下载{video_info.vid}视频超时: {video_link}, 跳过")
                        continue
                    except:
                        continue

                if response.status_code != 200:
                    continue
                else:
                    # 下载成功，写入文件
                    file_path = self.store_dir / video_info.user.nick / f"{video_info.vid}.mp4"
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    # 写入视频元数据
                    video_info_file_path = self.store_dir / video_info.user.nick / f"{video_info.vid}.json"
                    video_info.local_file_path = file_path
                    with open(video_info_file_path, "w") as f:
                        f.write(video_info.model_dump_json())
                    logger.info(f"下载{video_info.vid}视频成功: {file_path}")
                    return True
            else:
                continue
        logger.error(f"下载{video_info.vid}视频失败, 跳过")
        return False

    def get_local_video_list(self, nick: str='')->List[DouyinVideoInfo]:
        result = []
        
        for file in (self.store_dir/f"{nick}").glob(f"*.json"):
            with open(file, "r") as f:
                video_info = DouyinVideoInfo.model_validate_json(f.read())
                video_info.local_file_path = self.store_dir / video_info.user.nick / f"{video_info.vid}.mp4"
                result.append(video_info)
        return result

    def download_videos_with_thread_pool(self, video_list: List[DouyinVideoInfo], max_workers: int = 5) -> List[bool]:
        """
        使用线程池并发下载视频
        :param video_list: 要下载的视频列表
        :param max_workers: 最大线程数
        :return: 下载结果列表，True表示成功，False表示失败
        """
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有下载任务
            future_to_video = {executor.submit(self.download_video, video): video for video in video_list}
            
            # 处理完成的任务
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result:
                        logger.info(f"线程池下载视频成功: {video.vid}")
                    else:
                        logger.error(f"线程池下载视频失败: {video.vid}")
                except Exception as exc:
                    logger.error(f"线程池下载视频异常: {video.vid}, 异常: {exc}")
                    results.append(False)
        
        return results
    
    def merge_videos(self, nick: str, video_list: List[DouyinVideoInfo], ffmpeg_max_workers: int = 4)->bool:
        """
        合并视频列表中的所有视频（一次性合并，兼容 moviepy 设计）
        :param video_list: 要合并的视频列表
        :param ffmpeg_max_workers: ffmpeg最大线程数
        :return: 合并是否成功
        """
        # 按创建时间排序视频
        sorted_videos = sorted(video_list, key=lambda x: x.create_time, reverse=True)
        
        # 创建输出目录
        output_dir = self.store_dir / nick
        output_dir.mkdir(parents=True, exist_ok=True)

        # 读取上一次合并的视频列表
        merged_video_record_file_path = output_dir / ".merged_videos.txt"
        if merged_video_record_file_path.exists():
            with open(merged_video_record_file_path, "r") as f:
                merged_videos = [line.strip() for line in f.read().splitlines()]
        else:
            merged_videos = []

        # 过滤掉已经合并的视频
        sorted_videos = [video for video in sorted_videos if video.vid not in merged_videos]

        if not sorted_videos:
            logger.info(f"没有需要合并的视频")
            return True
        
        # 首先需要先对每个视频进行统一的尺寸处理, 强制处理成1080x1920
        logger.info(f"开始转码视频: {len(sorted_videos)} 个")
        for video_info in tqdm(sorted_videos):
            # 对视频转码
            logger.info(f"开始转码视频: {video_info.vid}")
            resize_video_path = output_dir / f"{video_info.vid}-resized.mp4"
            if resize_video_path.exists():
                logger.info(f"转码视频: {video_info.vid} 已存在: {resize_video_path}")
            else:
                os.system(f'ffmpeg -i {video_info.local_file_path} \
                       -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" \
                               -r 30 -c:v libx264 -profile:v high -preset fast -crf 23 \
                               -c:a aac -b:a 128k -ar 44100 -ac 2 \
                               -movflags +faststart -threads {ffmpeg_max_workers} {str(resize_video_path)}')
            video_info.resize_video_path = resize_video_path
            logger.info(f"转码视频: {video_info.vid} 成功: {resize_video_path}")

        # 对视频文件进行合并
        merged_video_path = self.store_dir / f"{nick}.mp4"
        # 创建一个filelist.txt文件
        with open(output_dir / ".filelist.txt", "w") as f:
            
            for video_info in sorted_videos:
                f.write(f"file '{str(video_info.resize_video_path)}'\n")
            # 原来的视频拼接在后面
            if merged_video_path.exists():
                f.write(f"file '{str(merged_video_path)}'\n")

        # 使用ffmpeg合并视频
        temp_file_path = output_dir / ".temp.mp4"
        logger.info(f"开始合并视频...")
        os.system(f'ffmpeg -f concat -safe 0 -i {output_dir / ".filelist.txt"} -c copy -threads {ffmpeg_max_workers} {str(temp_file_path)}')
        # 删除原始文件，并重命名
        if merged_video_path.exists():
            os.remove(merged_video_path)
        os.rename(temp_file_path, merged_video_path)
        logger.info(f"视频合并成功: {merged_video_path}")
        # 写入已合并记录文件
        with open(merged_video_record_file_path, "w") as f:
            for video_info in sorted_videos:
                f.write(f"{video_info.vid}\n")
        return True

def main():
    # 加载配置
    config = load_config()
    users_config = config.get("users", [])
    ffmpeg_max_workers = config.get("ffmpeg_max_workers", 4)
    store_dir = config.get("store_dir", "data")
    
    if not users_config:
        logger.error("没有找到有效的用户配置，请检查 config.json 文件")
        return

    logger.info(f"使用存储目录: {store_dir}")
    logger.info(f"FFmpeg最大线程数: {ffmpeg_max_workers}")

    # 加载已下载的视频列表
    douyin_merger_core = DouyinMergerCore(store_dir)

    for user_config in users_config:
        nickname = user_config.get("nickname")
        sec_uid = user_config.get("sec_uid")
        
        if not nickname or not sec_uid:
            logger.error(f"用户配置不完整: {user_config}")
            continue
            
        logger.info(f"开始处理用户: {nickname}")
        
        local_video_list = douyin_merger_core.get_local_video_list(nickname)
        # 先获取所有视频item
        spider = DouyinVideoSpider(local_video_list)
        items = spider.get_post_list(nickname, sec_uid)
        items = list(items)
        logger.info(f"开始使用线程池下载 {len(items)} 个视频")
        download_results = douyin_merger_core.download_videos_with_thread_pool(items, max_workers=4)
    
        # 统计下载结果
        success_count = sum(download_results)
        total_count = len(download_results)
        logger.info(f"下载完成: 成功 {success_count}/{total_count} 个视频")

        # 开始合并视频
        items = douyin_merger_core.get_local_video_list(nickname)
        logger.info("开始合并视频")
        merge_success = douyin_merger_core.merge_videos(nickname, items, ffmpeg_max_workers)
        if merge_success:
            logger.info("视频合并成功")
    
    pass
    
if __name__ == "__main__":
    main()
