"""
rat.timetable.data — Initial club member schedule dataset and JSON persistence.
Populated from verified Ton Duc Thang University (TDTU) student timetables.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

from rat.timetable.model import ClassSession, MemberSchedule

logger = logging.getLogger("rat.timetable.data")

DATA_DIR = Path.home() / ".rat"
DATA_FILE = DATA_DIR / "club_schedules.json"

# Authentic TDTU Member Schedules Extracted from Portals & OCR
INITIAL_CLUB_MEMBERS = [
    {
        "id": "m1",
        "name": "Huỳnh Nhật Huy",
        "mssv": "523C0012",
        "major": "Công nghệ Thông tin",
        "color_hex": "#3b82f6",  # Blue
        "schedule": {
            "T2": [(1, 3, "Thực hành Giải tích ứng dụng CNTT 2", "A608"), (4, 6, "Giải tích ứng dụng CNTT 2", "F702")],
            "T3": [(7, 9, "Lập trình hàm", "F712"), (10, 12, "Thực hành Lập trình hàm", "A607")],
            "T4": [(4, 6, "Cấu trúc dữ liệu & giải thuật", "F702"), (7, 9, "Cấu trúc dữ liệu & giải thuật (Bù)", "C404")],
            "T5": [(1, 3, "Kỹ năng soạn thảo VB kỹ thuật", "C406"), (7, 9, "Giải tích ứng dụng CNTT", "F610")],
            "T6": [(1, 3, "Thực hành Giải tích ứng dụng CNTT", "A610"), (7, 9, "Thực hành Cấu trúc dữ liệu", "A707")],
            "T7": [],
            "CN": []
        }
    },
    {
        "id": "m2",
        "name": "Thành viên QTKD",
        "mssv": "K27-QTKD",
        "major": "Quản trị Kinh doanh / Tài chính",
        "color_hex": "#10b981",  # Emerald
        "schedule": {
            "T2": [],
            "T3": [(2, 6, "Quản lý sự thay đổi", "C411-A"), (7, 11, "Ứng dụng Big Data trong quản lý", "D0401-B")],
            "T4": [(1, 3, "HFIATA - Module 4 (Contract & Finance)", "C303"), (7, 9, "Khởi nghiệp & đổi mới sáng tạo", "D0306")],
            "T5": [],
            "T6": [],
            "T7": [(4, 6, "HFIATA - Module 4", "F707")],
            "CN": [(1, 3, "HFIATA - Module 4 (Online Bù)", "HOCTRUCTUYEN-3")]
        }
    },
    {
        "id": "m3",
        "name": "Phạm Vũ Thảo Nguyên",
        "mssv": "62500106",
        "major": "Khoa học Ứng dụng",
        "color_hex": "#ec4899",  # Pink
        "schedule": {
            "T2": [(10, 12, "GDTC 2 - Karate", "TRET-NTD-2"), (13, 15, "Sinh hoạt chủ nhiệm KHUD", "B406-A")],
            "T3": [(3, 6, "Hóa vô cơ", "C401"), (7, 9, "Hóa lý kỹ thuật 1", "B204")],
            "T4": [(1, 3, "Vẽ kỹ thuật", "B406-A"), (4, 6, "Nhập môn Phân tích Dữ liệu", "B406-B"), (7, 9, "Thực hành Vẽ kỹ thuật", "A703")],
            "T5": [(4, 6, "Kinh tế chính trị Mác-Lênin", "B204"), (7, 9, "Toán cao cấp trong KH sự sống", "C308")],
            "T6": [(1, 6, "Thí nghiệm Hóa đại cương", "C511")],
            "T7": [],
            "CN": []
        }
    },
    {
        "id": "m4",
        "name": "Thành viên Kiến trúc",
        "mssv": "K27-KT",
        "major": "Kiến trúc / Quy hoạch",
        "color_hex": "#f59e0b",  # Amber
        "schedule": {
            "T2": [(4, 6, "Vật liệu trong kiến trúc", "D0101-B"), (7, 9, "Nhập môn quy hoạch", "D0105-A")],
            "T3": [],
            "T4": [(10, 12, "Lịch sử kiến trúc Phương Đông & VN", "D0102-A")],
            "T5": [],
            "T6": [(7, 9, "Chuyên đề thiết nội thất", "D0101-A"), (10, 12, "Khoa học môi trường kiến trúc", "D0101-A")],
            "T7": [(1, 3, "Chuyên đề kiến trúc nhà công nghiệp", "D0101-A")],
            "CN": []
        }
    },
    {
        "id": "m5",
        "name": "Thành viên CNSH",
        "mssv": "K27-CNSH",
        "major": "Công nghệ Sinh học / Y sinh",
        "color_hex": "#8b5cf6",  # Violet
        "schedule": {
            "T2": [(1, 3, "Tiếng Anh 3", "P15H03"), (7, 9, "Vật liệu sinh học", "F702")],
            "T3": [(1, 6, "Thí nghiệm Genomic phân tử", "C511"), (7, 9, "Vi sinh vật và bệnh học", "F410")],
            "T4": [(1, 3, "Tiếng Anh 3", "P15H03")],
            "T5": [(1, 3, "Thiết kế & phân tích thí nghiệm", "F507")],
            "T6": [(1, 3, "Tiếng Anh 3", "P15H03"), (7, 11, "Miễn dịch học", "F610")],
            "T7": [],
            "CN": []
        }
    },
    {
        "id": "m6",
        "name": "Thông Ngọc Lan Anh",
        "mssv": "624H0001",
        "major": "Kỹ thuật Hóa học",
        "color_hex": "#06b6d4",  # Cyan
        "schedule": {
            "T2": [(1, 6, "Thí nghiệm Hóa hữu cơ", "C513")],
            "T3": [(1, 3, "Hóa học xanh", "F412"), (4, 6, "Lịch sử Đảng Cộng sản VN", "B411")],
            "T4": [(1, 3, "Hóa phân tích", "F512"), (4, 6, "Quản trị công nghiệp", "F701")],
            "T5": [(4, 6, "Hóa sinh", "C205")],
            "T6": [(4, 6, "Kỹ thuật phân riêng", "F712")],
            "T7": [(4, 6, "Vật liệu học", "F302"), (7, 12, "Thí nghiệm Hóa lý kỹ thuật", "C512")],
            "CN": []
        }
    }
]


def dict_to_member_schedule(d: dict) -> MemberSchedule:
    sched: Dict[str, List[ClassSession]] = {}
    raw_sched = d.get("schedule", {})
    for day, session_list in raw_sched.items():
        sched[day] = []
        for item in session_list:
            if isinstance(item, (list, tuple)):
                sched[day].append(ClassSession.from_tuple(tuple(item)))
            elif isinstance(item, dict):
                sched[day].append(ClassSession(
                    start_period=item.get("start", 1),
                    end_period=item.get("end", 1),
                    course_name=item.get("course", ""),
                    room=item.get("room", "")
                ))
    return MemberSchedule(
        id=d.get("id", ""),
        name=d.get("name", "Thành viên"),
        mssv=d.get("mssv", ""),
        major=d.get("major", ""),
        color_hex=d.get("color_hex", "#3b82f6"),
        schedule=sched,
        active=d.get("active", True)
    )


def member_schedule_to_dict(m: MemberSchedule) -> dict:
    sched_dict = {}
    for day, sessions in m.schedule.items():
        sched_dict[day] = [s.to_dict() for s in sessions]
    return {
        "id": m.id,
        "name": m.name,
        "mssv": m.mssv,
        "major": m.major,
        "color_hex": m.color_hex,
        "active": m.active,
        "schedule": sched_dict
    }


def get_default_club_members() -> List[MemberSchedule]:
    """Returns the baseline list of 6 TDTU club members."""
    return [dict_to_member_schedule(d) for d in INITIAL_CLUB_MEMBERS]


def load_club_members() -> List[MemberSchedule]:
    """Loads club members from ~/.rat/club_schedules.json or creates initial default."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        members = get_default_club_members()
        save_club_members(members)
        return members

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [dict_to_member_schedule(d) for d in data]
    except Exception as e:
        logger.error(f"Error loading {DATA_FILE}: {e}. Falling back to default.")
        return get_default_club_members()


def save_club_members(members: List[MemberSchedule]) -> None:
    """Saves club members to ~/.rat/club_schedules.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        raw_list = [member_schedule_to_dict(m) for m in members]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(raw_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving {DATA_FILE}: {e}")
