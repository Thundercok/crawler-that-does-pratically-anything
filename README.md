# 🐭 rat (Retrieval Augmented Tool) — macOS Smart Assistant

> **Ứng dụng quản trị tệp tin ngữ nghĩa đa phương thức, tìm kiếm siêu tốc (< 25ms) và trợ lý ghép thời khóa biểu nhóm/CLB tối ưu 100% On-Device cho macOS.**

---

## ⚡ Hướng Dẫn Cài Đặt Siêu Nhanh (Dành Cho Bạn Bè)

Bạn có thể chọn 1 trong 2 cách cài đặt cực kỳ đơn giản dưới đây:

### 💿 CÁCH 1: Dùng Bộ Cài Đặt `rat.dmg` (Khuyên Dùng cho Người Dùng Phổ Thông)
1. Tải file **`rat.dmg`** từ đường dẫn chia sẻ của nhóm.
2. Mở file DMG, bạn sẽ thấy 2 mục chính:
   - **Kéo `rat.app` vào thư mục `Applications`** bên cạnh.
   - **Nhấp đúp vào file `Cài_Đặt_&_Mở_rat.command`**: File này sẽ tự động gỡ bỏ cờ hạn chế của Apple (Gatekeeper Quarantine) và khởi chạy app ngay lập tức!
3. Cấp quyền **Accessibility** (để phím tắt hoạt động) và **Full Disk Access** (để quét tệp) theo hướng dẫn trên màn hình.

---

### 💻 CÁCH 2: Cài Đặt 1-Click Bằng Mã Nguồn (Dành Cho Dân Dev / Sinh Viên)
Mở Terminal, đi vào thư mục dự án và gõ đúng **1 lệnh**:

```bash
./setup.sh
```

*(Hoặc: `bash scripts/setup.sh`)*

Script sẽ tự động 100%:
- ✅ Kiểm tra macOS và phiên bản Python (>= 3.10).
- ✅ Tự tạo môi trường ảo `.venv` độc lập (tuân thủ chuẩn bảo mật PEP 668).
- ✅ Cài đặt toàn bộ thư viện cần thiết từ `requirements.txt`.
- ✅ Chạy tự chẩn đoán (Self-test) đảm bảo mọi tính năng hoạt động trơn tru.
- ✅ Tích hợp phím tắt lệnh `rat` vào `~/.zshrc` (chỉ cần gõ `rat` ở bất cứ đâu để mở app).

---

## 🌟 Tính Năng Nổi Bật & Phím Tắt

| Tính Năng | Thao Tác / Phím Tắt | Mô Tả |
| :--- | :--- | :--- |
| ⚡ **Spotlight HUD Nổi** | **`Option + Shift + Space`** | Tìm kiếm tệp tức thì (< 25ms), không chiếm diện tích màn hình. |
| 🗂️ **AI Finder Đầy Đủ** | Mở app trực tiếp | Xem trước văn bản, slide, ảnh OCR, tóm tắt và hỏi đáp nội dung. |
| 📅 **Ghép TKB CLB / Nhóm** | Menu Bar $\rightarrow$ **Thời khóa biểu CLB** | Nhập lịch các thành viên, ma trận tự động phát hiện **Khung giờ vàng** rảnh chung và xuất `.ics`. |
| 🖱️ **Trạng Thái Menu Bar** | Icon chuột trên thanh Top Bar | Quét lại tệp, kiểm tra số lượng vector, tùy chỉnh phím tắt và thư mục. |

---

## 🛠️ Yêu Cầu Hệ Thống
- **Hệ điều hành**: macOS 12 Monterey trở lên (Tương thích hoàn hảo Apple Silicon M1/M2/M3/M4 & Intel).
- **RAM**: Tối thiểu 4GB RAM (Khuyên dùng 8GB RAM trở lên).
- **Quyền hạn macOS**:
  - `Accessibility`: Lắng nghe phím tắt toàn cục.
  - `Full Disk Access`: Đọc và trích xuất nội dung tài liệu.
