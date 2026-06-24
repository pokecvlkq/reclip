# ReClip

Công cụ tải video và âm thanh self-hosted, mã nguồn mở với giao diện web tinh giản. Dán đường dẫn từ YouTube, TikTok, Instagram, Twitter/X và hơn 1000 trang web khác — tải xuống dưới dạng MP4 hoặc MP3.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

https://github.com/user-attachments/assets/419d3e50-c933-444b-8cab-a9724986ba05

![ReClip MP3 Mode](assets/preview-mp3.png)

## Tính năng

- Tải video từ hơn 1000 trang web được hỗ trợ (thông qua [yt-dlp](https://github.com/yt-dlp/yt-dlp))
- Xuất video MP4 hoặc trích xuất âm thanh MP3
- Trình chọn chất lượng/độ phân giải
- Tải hàng loạt — dán nhiều đường dẫn cùng lúc
- Tự động loại bỏ các đường dẫn trùng lặp
- Giao diện tinh giản, phản hồi tốt — không dùng framework, không cần bước build
- Backend chỉ với một file Python duy nhất (~150 dòng)

## Khởi động nhanh

```bash
# Cài đặt yt-dlp và ffmpeg:
# macOS: brew install yt-dlp ffmpeg
# Windows: winget install yt-dlp ffmpeg (hoặc dùng scoop)
# Linux: apt install ffmpeg && pip install yt-dlp

git clone https://github.com/averygan/reclip.git
cd reclip
./reclip.sh
```

Mở **http://localhost:8899**.

Hoặc sử dụng Docker:

```bash
docker build -t reclip . && docker run -p 8899:8899 reclip
```

## Hướng dẫn sử dụng

1. Dán một hoặc nhiều đường dẫn video vào ô nhập liệu
2. Chọn định dạng **MP4** (video) hoặc **MP3** (âm thanh)
3. Nhấp vào **Tải thông tin** để tải thông tin video và ảnh thu nhỏ (thumbnail)
4. Chọn chất lượng/độ phân giải nếu có sẵn
5. Nhấp vào **Tải xuống** cho từng video riêng lẻ, hoặc **Tải tất cả**

## Các trang web được hỗ trợ

Bất kỳ trang web nào được [yt-dlp hỗ trợ](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md), bao gồm:

YouTube, TikTok, Instagram, Twitter/X, Reddit, Facebook, Vimeo, Twitch, Dailymotion, SoundCloud, Loom, Streamable, Pinterest, Tumblr, Threads, LinkedIn, và nhiều trang khác.

## Công nghệ sử dụng

- **Backend:** Python + Flask (~150 dòng)
- **Frontend:** Vanilla HTML/CSS/JS (một file duy nhất, không cần bước build)
- **Engine tải xuống:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [ffmpeg](https://ffmpeg.org/)
- **Thư viện phụ thuộc:** 2 (Flask, yt-dlp)

## Tuyên bố từ chối trách nhiệm

Công cụ này chỉ dành cho mục đích sử dụng cá nhân. Vui lòng tôn trọng luật bản quyền và điều khoản dịch vụ của các nền tảng mà bạn tải nội dung xuống. Các nhà phát triển không chịu trách nhiệm cho bất kỳ hành vi lạm dụng hoặc sử dụng sai mục đích công cụ này.

## Giấy phép

[MIT](LICENSE)
