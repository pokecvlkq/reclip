# Changelog

## [2026-06-24]
### Added
- Thêm tệp kiểm thử tự động `test_app.py` với 13 trường hợp kiểm thử (100% PASS).
- Thêm cơ chế dọn dẹp đĩa tự động (daemon thread) quét xóa file downloads và jobs cũ hơn 1 giờ trong `app.py`.
- Thêm khóa an toàn đa luồng `threading.Lock()` cho quản lý jobs.
- Bổ sung hướng dẫn cài đặt môi trường cho Windows trong `README.md`.

### Changed
- Việt hóa toàn bộ tài liệu `README.md`.
- Việt hóa 7 thông báo lỗi backend trong `app.py`.
- Việt hóa toàn bộ text giao diện và các thông báo lỗi trên UI trong `templates/index.html`.
- Nâng cấp giao diện sang Dark Mode Premium (nền tối sâu `#0f0f11`, hiệu ứng glassmorphism, viền trong suốt mỏng, font chữ Inter, logo gradient cam-hồng, hover glow).
- Tối ưu hóa tải nhiều link song song bằng `Promise.all` thay vì lặp tuần tự.

### Fixed
- Vá lỗi bảo mật *Argument Injection* bằng cách kiểm tra tiền tố URL đầu vào bắt đầu bằng `http://` hoặc `https://`.
