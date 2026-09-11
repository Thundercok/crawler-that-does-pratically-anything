# 🚀 CLAUDE MASTER PROMPT: HANDOFF & FUTURE ARCHITECTURAL ROADMAP FOR 'RAT'
> **Dự án**: `rat` (Retrieval Augmented Tool) — Ứng dụng Quản trị Tệp tin Ngữ nghĩa Đa phương thức & Trợ lý Sinh viên / Nhóm bạn trên macOS.  
> **Người nhận tài liệu**: Claude (Senior Principal Architect & macOS System Specialist).  
> **Mục tiêu**: Định hình chiến lược, thiết kế kiến trúc và lộ trình tính năng thế hệ tiếp theo để biến ứng dụng thành một siêu công cụ mạnh mẽ, mượt mà và thực dụng nhất cho bạn bè & sinh viên.

---

## 📋 HƯỚNG DẪN DÀNH CHO CLAUDE (PROMPT SYSTEM)

```text
Bạn là một Senior Principal macOS Software Architect và Product Strategist chuyên sâu về On-Device AI, Local Information Retrieval (IR) và macOS Native Applications.

Tôi đang phát triển ứng dụng mang tên "rat" (Retrieval Augmented Tool) dành tặng bạn bè, thành viên câu lạc bộ và sinh viên đại học (cụ thể là macOS power users). Ứng dụng đã hoàn thiện nền tảng cốt lõi (Core Search, OCR Apple Vision, Timetable Compositor, Raycast-style Spotlight & Finder UI, 59/59 Tests Pass). 

Mục tiêu hiện tại: Tôi muốn phát triển ứng dụng này lên một tầm cao mới — cực kỳ "MẠNH MẼ" (robust, feature-rich, high-performance, thiết thực và đem lại giá trị vượt trội trong công việc & học tập hàng ngày).

Hãy đọc kỹ bức tranh toàn cảnh về kiến trúc hiện tại, các số liệu benchmark thực nghiệm và định hướng dưới đây, sau đó tư vấn chiến lược, phản biện kiến trúc và đề xuất Roadmap tính năng đột phá cho giai đoạn tiếp theo.
```

---

## 🏛️ 1. HIỆN TRẠNG DỰ ÁN & KIẾN TRÚC ĐÃ HOÀN THIỆN

### 1.1. Triết lý Thiết kế Cốt lõi (Core Philosophy)
1. **100% On-Device & Zero-Cloud Obligation**: Toàn bộ dữ liệu của bạn bè được bảo mật tuyệt đối trên máy cá nhân. Không bắt buộc cài Ollama hay GPU rời — máy Mac 8GB RAM vẫn chạy mượt mà tức thì.
2. **Độ trễ cấp độ Raycast/Spotlight**: Tìm kiếm ngữ nghĩa lai ghép trả kết quả trong **< 70ms**, hỏi đáp trích xuất nhanh trong **< 0.2ms**.
3. **Deep macOS Integration**: Tận dụng tối đa phần cứng Apple Silicon (Apple Neural Engine qua `Vision.framework`, `PDFKit`, `FSEvents`, xattr metadata).

---

### 1.2. Các Phân Hệ Đã Xây Dựng Hoàn Chỉnh

```
Spider-The-Web-Crawler/
├── rat/
│   ├── config.py                 # Cấu hình đa tầng (Paths, Hotkeys, DB, AI Models, Watch Dirs)
│   ├── main.py                   # Điểm khởi động: CLI, Resident App, Daemon, Spotlight, Schedule
│   ├── cli.py                    # Rich Terminal CLI (search, index, ask, dedup, status)
│   ├── crawler/
│   │   ├── db.py                 # SQLite WAL, FTS5 Virtual Table (unicode61), Compound Indexes
│   │   ├── indexer.py            # Đa luồng thu thập & bóc tách file, MD5 deduplication, chunking
│   │   ├── extractors.py         # Trích xuất sâu: PDFKit Scan OCR, DOCX, PPTX Image OCR, XLSX, Code AST
│   │   ├── apple_vision.py       # PyObjC Vision.framework (VNRecognizeTextRequest + VNClassifyImage)
│   │   ├── provenance.py         # macOS xattr (kMDItemWhereFroms: URL tải, app tải Telegram/Safari)
│   │   ├── watcher.py            # FSEvents real-time kernel file watcher (watchdog)
│   │   └── dedup.py              # Semantic Document Revision Trees (Bao_cao_v1 -> final)
│   ├── engine/
│   │   ├── hybrid_search.py      # M-RRF: SQLite FTS5 BM25 + Vector Cache + Recency Boosting
│   │   ├── vector_cache.py       # In-Memory Cosine Similarity Cache (< 1.5ms cho 50.000 vectors)
│   │   ├── embedder.py           # FastEmbed (BAAI/bge-small-en-v1.5) ONNX Runtime ARM64
│   │   ├── corrective_retriever.py # FR-CoT (Fast Reasoning Chain-of-Thought) đa bước
│   │   ├── qa_engine.py          # Multi-Tier Router: Extractive (<0.2ms) -> Local SLM -> Cloud LLM
│   │   └── slm.py                # Ollama/MLX integration với TTL Cache & Few-shot Prompts
│   ├── timetable/                # [MỚI] Module Xử lý & Ghép Thời Khóa Biểu
│   │   ├── model.py              # Schema: TDTU_PERIODS (15 tiết, 5 ca), GoldenWindow, MemberSchedule
│   │   ├── data.py               # Quản lý & nạp dữ liệu TKB thành viên nhóm/CLB
│   │   └── compositor.py         # Thuật toán ma trận rảnh/bận, nhận diện "Khung giờ vàng", xuất .ics
│   ├── ui/
│   │   ├── spotlight_window.py   # Raycast-style floating search bar (Option+Shift+Space)
│   │   ├── finder_window.py      # macOS Sequoia AI Finder (Splitter, Preview, CoT Trace, Chat)
│   │   ├── schedule_window.py    # [MỚI] Giao diện Ghép TKB Pastel, Heatmap ma trận, 1-click sync
│   │   ├── onboarding_dialog.py  # [MỚI] Wizard xin quyền macOS Accessibility & Full Disk Access
│   │   ├── preview_panel.py      # Quick Look, Code highlighting, Linear-style metadata chips
│   │   └── theme.py              # Apple Human Interface Guidelines Dark/Light palette
│   └── os/
│       ├── hotkey.py             # Global Event Tap hotkeys không xung đột bộ gõ tiếng Việt
│       ├── menu_bar.py           # Native NSStatusBar indicator (Rescan, Quick open, Stats)
│       └── daemon.py             # LaunchAgent daemon (tự khởi động cùng hệ điều hành)
├── tests/                        # 59/59 Test Cases PASS (Unit tests, UI tests, Compositor tests)
└── scripts/
    ├── build_app.sh              # Script build 1-click ra .app và .dmg
    ├── tdtu_schedule_merger.py   # Script CLI ghép TKB sinh viên TDTU
    └── run_resource_profiler.py  # Công cụ benchmark tự động độ trễ & RAM
```

---

### 1.3. Báo Cáo Hiệu Năng Thực Tế (Profiling & Benchmarks)

* **Tập dữ liệu thử nghiệm**: **6.136 tệp tin thực tế** (~1.75 GB) trên macOS (Downloads, Documents, Code, PDF, PPTX).
* **Search Latency (End-to-End FR-CoT)**:
  - Median (p50): **64.35 ms**
  - 95th Percentile (p95): **96.23 ms**
  - In-Memory Vector Similarity (1.000 vectors): **1.2 ms** (Dung lượng RAM mảng vector chỉ tốn **4.88 MB**).
  - Offline Extractive Fact Extraction: **0.18 ms** (hoàn toàn không cần LLM).
* **Tiêu thụ Bộ nhớ (RAM Footprint)**:
  - Chạy ngầm (Watcher + Menu Bar): **~80 MB – 110 MB RAM**.
  - Mở toàn bộ AI Finder + Vector Cache nạp sẵn: **~260 MB – 308 MB RAM** (chỉ chiếm **~3.5% trên MacBook 8GB RAM**).
* **Độ ổn định mã nguồn**: **59/59 Test Cases PASS** (`python3 -m unittest discover -s tests`).

---

## 🎯 2. MỤC TIÊU PHÁT TRIỂN: LÀM SAO ĐỂ APP TRỞ NÊN "CỰC KỲ MẠNH MẼ"?

Tôi đang trực tiếp bàn giao hoặc chia sẻ ứng dụng này cho **bạn bè, bạn cùng phòng, bạn cùng CLB, sinh viên trường (như TDTU và các trường ĐH khác)**. Tôi muốn khi họ dùng `rat`, họ phải thốt lên: *"App này đỉnh và tiện hơn Spotlight/Raycast nhiều!"*.

Để đạt được điều đó, tôi xác định 4 trụ cột chiến lược cần nâng cấp:

---

### 🏛️ Trụ cột 1: Siêu công cụ Tự động hóa Tệp tin Học tập & Làm việc (Intelligent File Copilot)
* **Vấn đề của bạn bè**: Thư mục `Downloads` và `Desktop` luôn là "bãi rác" khổng lồ (hàng trăm file slide bài giảng, đề thi PDF, file zip, ảnh chụp màn hình, hóa đơn chuyển khoản không tên rõ ràng).
* **Tiềm năng phát triển**:
  1. **Smart Auto-Organizer (Bộ dọn dẹp & sắp xếp thông minh)**: Tự động phân tích nội dung/OCR của file vừa tải về và gợi ý (hoặc tự động di chuyển) vào đúng thư mục môn học: `~/Documents/Hoc_Tap/HK1_2026/Giai_Tich/` hoặc `~/Documents/Hoa_Don/`.
  2. **Semantic Bulk Actions**: Cho phép gõ lệnh tự nhiên trong Spotlight: *"Gom tất cả slide môn Cấu trúc dữ liệu tuần 3 vào thư mục OnTap"* hoặc *"Xóa tất cả file trùng lặp cũ chỉ giữ lại bản Final"*.
  3. **Instant Action Menu (Raycast-grade)**: Nhấn `Tab` hoặc `Cmd+K` trên bất kỳ kết quả tìm kiếm nào để: Copy đường dẫn, AirDrop cho bạn bè, Nén zip, Tóm tắt nội dung bằng 3 gạch đầu dòng, hoặc mở trong Terminal.

---

### 🏛️ Trụ cột 2: Hệ Sinh Thái Trợ Lý Sinh Viên & Đội Nhóm (Academic & Group Companion)
* **Thành tựu hiện tại**: Đã có `rat.timetable` và giao diện `ScheduleWindow` ghép TKB 6 thành viên, tìm Khung Giờ Vàng (Golden Windows) và xuất `.ics`.
* **Tiềm năng nâng cấp vượt bậc**:
  1. **AI / Vision TKB Parser (One-Shot Schedule Ingestion)**: Cho phép bạn bè chỉ cần kéo-thả ảnh chụp màn hình TKB cổng trường (hoặc tải file PDF/Excel TKB từ web trường) vào `rat` → Apple Vision OCR tự động bóc tách thành lịch học của cá nhân trong 2 giây mà không cần nhập thủ công.
  2. **Hỗ trợ Đa Trường Đại học**: Mở rộng từ định dạng tiết của TDTU sang cấu hình linh hoạt (ĐHQG HCM, Bách Khoa, Kinh Tế, FPT...) thông qua Time Grid Config đa năng.
  3. **Deadline & Assignment Sentinel (Quản lý Hạn nộp bài & Lịch thi)**: Tự động quét các file đề cương bài tập lớn, syllabus, email thông báo thi để trích xuất deadline, hiển thị đếm ngược (countdown) trực tiếp trên Menu Bar và gửi cảnh báo trước 24h.
  4. **P2P / Local Group Sync**: Cơ chế đồng bộ lịch nhóm siêu nhẹ (Local Network / QR Code / Cloudflare KV / Shared Link) để bạn bè chỉ cần quét QR là ghép được lịch cả nhóm đi học bù, làm bài tập lớn hoặc đi cà phê.

---

### 🏛️ Trụ cột 3: Khả năng Tương tác Ngôn ngữ Tự nhiên & Multi-Document Chat
* **Hiện tại**: Có chế độ Extractive Q&A siêu tốc và kết nối Local SLM (`qwen2.5`) / Cloud LLM.
* **Nâng cấp "Mạnh mẽ"**:
  1. **Multi-Document Synthesis (Hỏi đáp tổng hợp nhiều tài liệu)**: Chọn 3 file slide khác nhau hoặc toàn bộ tài liệu ôn thi một môn, sau đó hỏi: *"So sánh sự khác biệt giữa thuật toán Dijkstra và Bellman-Ford dựa trên các slide đã học"*.
  2. **Smart Flashcard & Exam Prep Generator**: Tự động sinh bộ câu hỏi trắc nghiệm / câu hỏi ôn thi kèm đáp án từ tài liệu đã chọn, cho phép bạn bè tự kiểm tra kiến thức trước giờ thi.
  3. **Zero-Latency In-Situ Quick Summary**: Xem tóm tắt 30 giây ngay tại bảng Preview Panel mà không cần mở file lên xem.

---

### 🏛️ Trụ cột 4: Trải nghiệm macOS Native "Chuẩn Apple" & Phân phối Đóng gói (Zero-Friction Distribution)
* **Hiện tại**: Đã có `scripts/build_app.sh` (PyInstaller) và `onboarding_dialog.py`.
* **Cần hoàn thiện để người không rành kỹ thuật tải về dùng được ngay**:
  1. **Tối ưu hóa Bundle Size & Cold Start**: Làm sao để file `.dmg` nhỏ gọn nhất, khởi động trong nháy mắt mà không bị crash do thiếu dynamic library trên máy Mac khác.
  2. **Notarization & Gatekeeper Handling**: Hướng dẫn bạn bè vượt qua cảnh báo "App can't be opened because it is from an unidentified developer" một cách thanh lịch hoặc cơ chế ad-hoc codesigning an toàn.
  3. **Lộ trình Chuyển dịch Công nghệ (Tech Stack Evolution)**: Đánh giá khả năng viết native Swift / Tauri / Rust wrapper cho tầng UI và Hotkeys, trong khi giữ Python Core làm background service, hoặc giữ nguyên PyQt6 nhưng tối ưu tối đa.

---

## ❓ NHỮNG CÂU HỎI & YÊU CẦU CLAUDE TƯ VẤN CỤ THỂ

Claude thân mến, dựa trên toàn bộ bối cảnh trên, hãy đưa ra một bản phân tích chiến lược toàn diện gồm các phần sau:

1. **Đánh Giá & Phản Biện Kiến Trúc Hiện Tại**:
   - Kiến trúc hiện tại của `rat` có những điểm mạnh gì độc đáo so với Raycast, Alfred hay Apple Spotlight?
   - Những "nút thắt cổ chai" (bottlenecks) tiềm ẩn nào về hiệu năng, bộ nhớ hoặc độ tin cậy khi người dùng cài đặt lâu dài trên macOS?

2. **Thiết Kế Chi Tiết cho 3 Tính Năng "Game Changer" Nhất**:
   - *Tính năng A*: **One-Click Vision OCR Schedule Ingestion** (Kéo thả ảnh TKB → Tự bóc tách ra ma trận lịch trình). Thiết kế giải thuật phân tích tọa độ bounding box OCR để map vào lưới thời gian (tiết/thứ/phòng học).
   - *Tính năng B*: **Smart Downloads Janitor & Academic Organizer** (Tự nhận diện và gợi ý phân loại tài liệu vào thư mục môn học theo ngữ nghĩa).
   - *Tính năng C*: **Deep Quick Actions Engine (Raycast-style Command Palette)**: Kiến trúc thiết kế hệ thống phím tắt hành động mở rộng (Plugins/Actions) để thao tác trên tệp.

3. **Lộ Trình Phát Triển (Actionable Roadmap) Theo Giai Đoạn**:
   - **Sprint 1 (Immediate - 1 đến 2 tuần)**: Những cải tiến nhanh (Quick Wins) nào mang lại cảm giác "mạnh mẽ" tức thì cho bạn bè khi sử dụng hàng ngày?
   - **Sprint 2 (Medium-term - 1 tháng)**: Xây dựng các tính năng nâng cao về học tập & làm việc nhóm.
   - **Sprint 3 (Long-term - 2-3 tháng)**: Tối ưu phân phối, đóng gói `.dmg`, và kiến trúc tương lai.

4. **Lời khuyên về Trải nghiệm Người Dùng (UX/DX) cho bạn bè**:
   - Làm thế nào để một người bạn không rành công nghệ, chỉ biết dùng máy Mac cơ bản, cảm thấy thoải mái và yêu thích sử dụng `rat` ngay từ phút đầu tiên?
