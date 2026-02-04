import os
from tiktok_scraper import TikTokScraper
import config


def print_menu():
    """Hiển thị menu"""
    print(f"\n{'='*60}")
    print(f"🎵 TIKTOK SCRAPER")
    print(f"{'='*60}")
    print(f"   Kênh: @{config.CHANNEL}")
    print(f"   Min views: {config.MIN_PLAYS:,}")
    print(f"   Min likes: {config.MIN_LIKES:,}")
    print(f"{'='*60}")
    print("\n📋 MENU:")
    print("   1. Crawl video (lấy danh sách video)")
    print("   2. Tải video")
    print("   3. Cấu hình")
    print("   0. Thoát")
    print()


def config_menu():
    """Menu cấu hình"""
    while True:
        print(f"\n{'='*60}")
        print(f"⚙️  CẤU HÌNH HIỆN TẠI")
        print(f"{'='*60}")
        print(f"   1. Kênh: @{config.CHANNEL}")
        print(f"   2. Min views: {config.MIN_PLAYS:,}")
        print(f"   3. Min likes: {config.MIN_LIKES:,}")
        print(f"   0. Quay lại")
        print()

        choice = input("Chọn mục cần thay đổi (0-3): ").strip()

        if choice == "0":
            break
        elif choice == "1":
            new_channel = input("Nhập tên kênh mới (không có @): ").strip()
            if new_channel:
                config.CHANNEL = new_channel
                print(f"✅ Đã đổi kênh thành @{new_channel}")
        elif choice == "2":
            try:
                new_min = int(input("Nhập min views (0 = không lọc): ").strip())
                config.MIN_PLAYS = max(0, new_min)
                print(f"✅ Đã đặt min views = {config.MIN_PLAYS:,}")
            except ValueError:
                print("❌ Vui lòng nhập số")
        elif choice == "3":
            try:
                new_min = int(input("Nhập min likes (0 = không lọc): ").strip())
                config.MIN_LIKES = max(0, new_min)
                print(f"✅ Đã đặt min likes = {config.MIN_LIKES:,}")
            except ValueError:
                print("❌ Vui lòng nhập số")


def get_output_path():
    """Lấy đường dẫn file JSON output"""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    return os.path.join(config.DATA_DIR, f"{config.CHANNEL}.json")


def get_download_base_dir():
    """Lấy đường dẫn thư mục gốc download: videos_download/{CHANNEL}"""
    return os.path.join("videos_download", config.CHANNEL)


def crawl_videos():
    """Crawl video từ kênh"""
    profile_url = f"https://www.tiktok.com/@{config.CHANNEL}"

    scraper = TikTokScraper(
        profile_url,
        min_plays=config.MIN_PLAYS,
        min_likes=config.MIN_LIKES
    )

    scraper.fetch_videos()
    scraper.print_summary()

    output_path = get_output_path()
    scraper.save_to_json(output_path)

    return scraper


def download_videos(scraper: TikTokScraper = None):
    """Tải video (chất lượng tốt nhất, không watermark)"""
    if not scraper or not scraper.videos:
        print("\n⚠️  Chưa có danh sách video. Đang crawl...")
        scraper = crawl_videos()

    if not scraper.videos:
        print("❌ Không có video nào để tải")
        return

    print(f"\n📥 Có {len(scraper.videos)} video sẵn sàng để tải")

    scraper.download_videos_via_api(base_dir=get_download_base_dir())


def main():
    scraper = None

    while True:
        print_menu()
        choice = input("Chọn chức năng (0-3): ").strip()

        if choice == "0":
            print("\n👋 Tạm biệt!\n")
            break
        elif choice == "1":
            scraper = crawl_videos()
        elif choice == "2":
            download_videos(scraper)
        elif choice == "3":
            config_menu()
        else:
            print("❌ Lựa chọn không hợp lệ")


if __name__ == "__main__":
    main()
