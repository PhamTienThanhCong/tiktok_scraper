import json
import subprocess
import re
import os
import requests
from datetime import datetime


class TikTokScraper:
    """
    Class để scrape video từ TikTok profile
    """

    def __init__(self, profile_url: str, min_plays: int = 0, min_likes: int = 0):
        """
        Khởi tạo scraper với URL profile

        Args:
            profile_url: URL profile TikTok (vd: https://www.tiktok.com/@username)
            min_plays: Số lượt xem tối thiểu để lọc video
            min_likes: Số lượt thích tối thiểu để lọc video
        """
        self.profile_url = profile_url
        self.username = self._extract_username()
        self.user_info = None
        self.videos = []
        self.min_plays = min_plays
        self.min_likes = min_likes

    def _extract_username(self) -> str:
        """Extract username từ URL"""
        match = re.search(r'tiktok\.com/@([^/?]+)', self.profile_url)
        if not match:
            raise ValueError("URL không hợp lệ. Vui lòng nhập URL dạng: https://www.tiktok.com/@username")
        return match.group(1)

    def fetch_videos(self) -> list:
        """
        Lấy toàn bộ video từ profile

        Returns:
            list: Danh sách video
        """
        print(f"\n{'='*60}")
        print(f"🎵 TikTok Profile Scraper")
        print(f"{'='*60}")
        print(f"📍 Username: @{self.username}")
        print(f"🎯 Lấy toàn bộ video")
        if self.min_plays > 0:
            print(f"🔍 Lọc: min views = {self.min_plays:,}")
        if self.min_likes > 0:
            print(f"🔍 Lọc: min likes = {self.min_likes:,}")
        print(f"{'='*60}\n")

        print("🔄 Đang lấy danh sách video...")

        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            self.profile_url
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                print(f"⚠️  yt-dlp error: {result.stderr[:500]}")
                return self._fetch_detailed()

            self._parse_output(result.stdout)
            print(f"✅ Tìm thấy {len(self.videos)} videos")
            return self.videos

        except subprocess.TimeoutExpired:
            print("❌ Timeout - quá trình lấy dữ liệu quá lâu")
            return []
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return []

    def _fetch_detailed(self) -> list:
        """Lấy thông tin chi tiết (fallback)"""
        print("🔄 Đang lấy thông tin chi tiết...")

        cmd = [
            "yt-dlp",
            "-j",
            "--no-download",
            self.profile_url
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            self._parse_output(result.stdout)
            return self.videos
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return []

    def _parse_output(self, output: str):
        """Parse output từ yt-dlp"""
        total_parsed = 0
        for line in output.strip().split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                total_parsed += 1

                # Extract user info từ video đầu tiên
                if not self.user_info and data.get("uploader"):
                    self.user_info = {
                        "uniqueId": data.get("uploader_id", self.username),
                        "nickname": data.get("uploader"),
                        "channel_url": data.get("channel_url"),
                    }

                # Lọc theo min_plays và min_likes
                play_count = data.get("view_count") or 0
                like_count = data.get("like_count") or 0

                if play_count < self.min_plays or like_count < self.min_likes:
                    continue

                video_info = {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "desc": data.get("description") or data.get("title"),
                    "url": data.get("url") or data.get("webpage_url"),
                    "duration": data.get("duration"),
                    "thumbnail": data.get("thumbnail"),
                    "stats": {
                        "playCount": play_count,
                        "diggCount": like_count,
                        "commentCount": data.get("comment_count"),
                        "shareCount": data.get("repost_count"),
                    },
                    "uploadDate": data.get("upload_date"),
                    "author": {
                        "uniqueId": data.get("uploader_id"),
                        "nickname": data.get("uploader"),
                    }
                }
                self.videos.append(video_info)

                if total_parsed % 50 == 0:
                    print(f"   📦 Đã xử lý {total_parsed} videos, lọc được {len(self.videos)}...")

            except json.JSONDecodeError:
                continue

    def save_to_json(self, filename: str = None) -> str:
        """
        Lưu kết quả ra file JSON

        Args:
            filename: Tên file (mặc định: tiktok_{username}_{timestamp}.json)

        Returns:
            str: Đường dẫn file đã lưu
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tiktok_{self.username}_{timestamp}.json"

        data = {
            "user": self.user_info,
            "videos": self.videos,
            "videoCount": len(self.videos),
            "filters": {
                "minPlays": self.min_plays,
                "minLikes": self.min_likes,
            },
            "scrapedAt": datetime.now().isoformat()
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Đã lưu kết quả vào {filename}")
        return filename

    def download_videos(self, output_dir: str = None, limit: int = None) -> int:
        """
        Tải video về máy

        Args:
            output_dir: Thư mục lưu video (mặc định: downloads/{username})
            limit: Số lượng video tối đa cần tải (None = tải hết)

        Returns:
            int: Số video đã tải thành công
        """
        if not self.videos:
            print("❌ Chưa có video nào. Hãy chạy fetch_videos() trước.")
            return 0

        if not output_dir:
            output_dir = f"downloads/{self.username}"

        os.makedirs(output_dir, exist_ok=True)

        videos_to_download = self.videos[:limit] if limit else self.videos
        total = len(videos_to_download)

        print(f"\n{'='*60}")
        print(f"📥 TẢI VIDEO")
        print(f"{'='*60}")
        print(f"📁 Thư mục: {output_dir}")
        print(f"🎬 Số video: {total}")
        print(f"{'='*60}\n")

        success_count = 0

        for i, video in enumerate(videos_to_download, 1):
            video_url = video.get("url")
            video_id = video.get("id")

            if not video_url:
                print(f"   ⚠️  [{i}/{total}] Không có URL cho video {video_id}")
                continue

            print(f"   🔄 [{i}/{total}] Đang tải video {video_id}...")

            cmd = [
                "yt-dlp",
                "-o", f"{output_dir}/%(id)s.%(ext)s",
                "--no-warnings",
                video_url
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    success_count += 1
                    print(f"   ✅ [{i}/{total}] Đã tải video {video_id}")
                else:
                    print(f"   ❌ [{i}/{total}] Lỗi tải video {video_id}")

            except subprocess.TimeoutExpired:
                print(f"   ⏱️  [{i}/{total}] Timeout video {video_id}")
            except Exception as e:
                print(f"   ❌ [{i}/{total}] Lỗi: {e}")

        print(f"\n{'='*60}")
        print(f"✅ Đã tải {success_count}/{total} videos")
        print(f"📁 Lưu tại: {output_dir}")
        print(f"{'='*60}")

        return success_count

    def get_video_urls(self) -> list:
        """Lấy danh sách URL của tất cả video"""
        return [v.get("url") for v in self.videos if v.get("url")]

    def get_stats(self) -> dict:
        """Lấy thống kê tổng hợp"""
        if not self.videos:
            return {}

        total_views = sum(v["stats"]["playCount"] or 0 for v in self.videos)
        total_likes = sum(v["stats"]["diggCount"] or 0 for v in self.videos)
        total_comments = sum(v["stats"]["commentCount"] or 0 for v in self.videos)
        total_shares = sum(v["stats"]["shareCount"] or 0 for v in self.videos)

        return {
            "totalVideos": len(self.videos),
            "totalViews": total_views,
            "totalLikes": total_likes,
            "totalComments": total_comments,
            "totalShares": total_shares,
            "avgViews": total_views // len(self.videos) if self.videos else 0,
            "avgLikes": total_likes // len(self.videos) if self.videos else 0,
        }

    def print_summary(self):
        """In tóm tắt kết quả"""
        if self.user_info:
            print(f"\n{'='*60}")
            print(f"👤 USER INFO")
            print(f"{'='*60}")
            print(f"   Username: @{self.user_info.get('uniqueId', 'N/A')}")
            print(f"   Nickname: {self.user_info.get('nickname', 'N/A')}")

        if self.videos:
            stats = self.get_stats()
            print(f"\n{'='*60}")
            print(f"📊 THỐNG KÊ")
            print(f"{'='*60}")
            print(f"   Tổng video: {stats['totalVideos']:,}")
            print(f"   Tổng views: {stats['totalViews']:,}")
            print(f"   Tổng likes: {stats['totalLikes']:,}")
            print(f"   Tổng comments: {stats['totalComments']:,}")
            print(f"   TB views/video: {stats['avgViews']:,}")
            print(f"   TB likes/video: {stats['avgLikes']:,}")

    # ============================================================
    # DOWNLOAD VIA API (no watermark)
    # ============================================================

    DOWNLOAD_API_URL = "https://www.tikwm.com/api/"
    
    def get_download_url_from_api(self, video_url: str, quality: str = "hd") -> dict | None:
        """
        Lấy URL download từ tikwm API (video không watermark)

        Args:
            video_url: URL video TikTok
            quality: "hd" (HD quality) hoặc "sd" (standard quality)

        Returns:
            dict với thông tin video hoặc None nếu lỗi
        """
        try:
            # Params cho tikwm.com
            params = {
                "url": video_url,
                "hd": 1  # Request HD quality
            }

            response = requests.post(
                self.DOWNLOAD_API_URL,
                data=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Kiểm tra response code
            if data.get('code') != 0:
                error_msg = data.get('msg', 'Unknown error')
                print(f"❌ API lỗi: {error_msg}")
                return None

            video_data = data.get('data', {})
            
            # Chọn download URL theo quality
            if quality == "hd" and video_data.get('hdplay'):
                download_url = video_data['hdplay']
            elif video_data.get('play'):
                download_url = video_data['play']
            else:
                print(f"❌ Không tìm thấy download URL")
                return None

            return {
                "download_url": download_url,
                "id": video_data.get('id'),
                "author": video_data.get('author', {}).get('nickname'),
                "unique_id": video_data.get('author', {}).get('unique_id'),
                "title": video_data.get('title', ''),
                "extension": "mp4"
            }

        except requests.RequestException as e:
            print(f"❌ Lỗi kết nối API: {e}")
            return None

    def download_video_via_api(self, video_url: str, output_dir: str, quality: str = "hd") -> bool:
        """
        Tải một video qua API (không watermark)

        Args:
            video_url: URL video TikTok
            output_dir: Thư mục lưu video
            quality: "hd" (HD quality) hoặc "sd" (standard quality)

        Returns:
            True nếu thành công, False nếu lỗi
        """
        info = self.get_download_url_from_api(video_url, quality)
        if not info:
            return False

        filename = f"{info['id']}.{info['extension']}"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            print(f"⏭️  Đã tồn tại: {filename}")
            return True

        try:
            print(f"📥 Đang tải: {info['title'][:50] if info['title'] else info['id']}...")
            response = requests.get(info["download_url"], timeout=120, stream=True)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"✅ Đã tải: {filename}")
            return True

        except requests.RequestException as e:
            print(f"❌ Lỗi tải video: {e}")
            return False

    def _load_checkpoint(self, checkpoint_path: str) -> set:
        """Tải danh sách video đã tải từ checkpoint"""
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        return set()

    def _save_checkpoint(self, checkpoint_path: str, downloaded_ids: set):
        """Lưu checkpoint"""
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(list(downloaded_ids), f, ensure_ascii=False, indent=2)

    def _load_failed_videos(self, failed_path: str) -> list:
        """Tải danh sách video lỗi"""
        if os.path.exists(failed_path):
            with open(failed_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_failed_videos(self, failed_path: str, failed_videos: list):
        """Lưu danh sách video lỗi"""
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed_videos, f, ensure_ascii=False, indent=2)

    def download_videos_via_api(self, base_dir: str = None, limit: int = None, quality: str = "hd") -> int:
        """
        Tải nhiều video qua API (không watermark)

        Args:
            base_dir: Thư mục gốc (mặc định: videos_download/{username})
                      Video sẽ lưu vào: {base_dir}/videos/
                      Checkpoint và fail_videos.json lưu vào: {base_dir}/
            limit: Số video tối đa (None = tất cả)
            quality: "hd" (HD quality) hoặc "sd" (standard quality)

        Returns:
            int: Số video tải thành công
        """
        if not self.videos:
            print("❌ Chưa có video nào. Hãy chạy fetch_videos() trước.")
            return 0

        if not base_dir:
            base_dir = f"videos_download/{self.username}"

        # Tạo cấu trúc thư mục
        videos_dir = os.path.join(base_dir, "videos")
        os.makedirs(videos_dir, exist_ok=True)

        # Đường dẫn checkpoint và fail_videos
        checkpoint_path = os.path.join(base_dir, "checkpoint.json")
        failed_path = os.path.join(base_dir, "fail_videos.json")

        # Tải checkpoint và failed videos
        downloaded_ids = self._load_checkpoint(checkpoint_path)
        failed_videos = self._load_failed_videos(failed_path)
        failed_ids = {v.get("id") for v in failed_videos}

        videos_to_download = self.videos[:limit] if limit else self.videos
        total = len(videos_to_download)
        success = 0
        failed = 0
        skipped = 0

        print(f"\n{'='*60}")
        print(f"📥 TẢI VIDEO (API - Không watermark)")
        print(f"{'='*60}")
        print(f"📁 Thư mục video: {videos_dir}")
        print(f"📋 Checkpoint: {checkpoint_path}")
        print(f"🎬 Tổng video: {total}")
        print(f"✅ Đã tải trước đó: {len(downloaded_ids)}")
        print(f"🎯 Chất lượng: {quality}")
        print(f"{'='*60}\n")

        for i, video in enumerate(videos_to_download, 1):
            video_url = video.get("url")
            video_id = video.get("id")

            if not video_url:
                print(f"⚠️  [{i}/{total}] Không có URL")
                failed += 1
                continue

            # Bỏ qua nếu đã tải
            if video_id and video_id in downloaded_ids:
                print(f"⏭️  [{i}/{total}] Đã tải: {video_id}")
                skipped += 1
                continue

            print(f"[{i}/{total}] ", end="")
            if self.download_video_via_api(video_url, videos_dir, quality):
                success += 1
                # Cập nhật checkpoint
                if video_id:
                    downloaded_ids.add(video_id)
                    self._save_checkpoint(checkpoint_path, downloaded_ids)
                    # Xóa khỏi failed nếu có
                    if video_id in failed_ids:
                        failed_videos = [v for v in failed_videos if v.get("id") != video_id]
                        self._save_failed_videos(failed_path, failed_videos)
            else:
                failed += 1
                # Thêm vào failed_videos
                if video_id and video_id not in failed_ids:
                    failed_videos.append({
                        "id": video_id,
                        "url": video_url,
                        "title": video.get("title"),
                        "error_time": datetime.now().isoformat()
                    })
                    self._save_failed_videos(failed_path, failed_videos)

        print(f"\n{'='*60}")
        print(f"📊 KẾT QUẢ:")
        print(f"   ✅ Thành công: {success}")
        print(f"   ⏭️  Đã có sẵn: {skipped}")
        print(f"   ❌ Thất bại: {failed}")
        print(f"📁 Video: {videos_dir}")
        print(f"📋 Checkpoint: {checkpoint_path}")
        if failed > 0:
            print(f"⚠️  Xem lỗi: {failed_path}")
        print(f"{'='*60}")

        return success
