"""
rat.timetable.compositor — Calculation Engine for Multi-Member Timetable Merging.
Calculates availability matrices, extracts Golden Windows, and exports to iCalendar / Chat format.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from rat.timetable.model import (
    DAYS,
    SHIFTS,
    TDTU_PERIODS,
    GoldenWindow,
    MemberSchedule,
    ShiftAvailability,
)


def availability_to_color(ratio: float) -> Dict[str, str]:
    """
    Chill Pastel Palette styling mapper according to availability ratio.
    """
    if ratio >= 0.99:
        # 100% Free — Matcha Latte Green
        return {
            "bg": "#dcfce7",
            "bg_hover": "#bbf7d0",
            "border": "#86efac",
            "text": "#166534",
            "badge": "🌿 100%",
            "desc": "Cả nhóm đều rảnh",
        }
    elif ratio >= 0.79:
        # 80%+ Free — Warm Honey / Butter Yellow
        return {
            "bg": "#fef3c7",
            "bg_hover": "#fde68a",
            "border": "#fde047",
            "text": "#854d0e",
            "badge": "☀️ Đa số",
            "desc": "Hầu hết đều rảnh",
        }
    elif ratio >= 0.49:
        # 50%+ Free — Soft Lavender / Lilac
        return {
            "bg": "#ede9fe",
            "bg_hover": "#ddd6fe",
            "border": "#c4b5fd",
            "text": "#5b21b6",
            "badge": "✨ Một nửa",
            "desc": "Khoảng nửa nhóm rảnh",
        }
    else:
        # < 50% Free — Quiet Cloud Gray
        return {
            "bg": "#f8fafc",
            "bg_hover": "#f1f5f9",
            "border": "#e2e8f0",
            "text": "#94a3b8",
            "badge": "🌧️ Kẹt lịch",
            "desc": "Đa số bận học",
        }


class TimetableCompositor:
    """Engine merging member schedules and computing availability."""

    def __init__(self, members: Optional[List[MemberSchedule]] = None) -> None:
        self.members: List[MemberSchedule] = members or []

    @property
    def active_members(self) -> List[MemberSchedule]:
        return [m for m in self.members if m.active]

    def set_member_active(self, member_id: str, active: bool) -> None:
        for m in self.members:
            if m.id == member_id:
                m.active = active
                break

    def toggle_member(self, member_id: str) -> bool:
        for m in self.members:
            if m.id == member_id:
                m.active = not m.active
                return m.active
        return False

    def compute_shift_matrix(self) -> Dict[str, Dict[str, ShiftAvailability]]:
        """
        Computes availability for each of the 5 Shifts across 7 Days.
        Returns: { day_code: { shift_id: ShiftAvailability } }
        """
        active = self.active_members
        total_active = len(active)
        matrix: Dict[str, Dict[str, ShiftAvailability]] = {}

        for day_code, day_name, _ in DAYS:
            matrix[day_code] = {}
            for shift_id, shift_name, time_range, (start_p, end_p) in SHIFTS:
                free_members: List[str] = []
                busy_details: List[Dict[str, str]] = []

                if total_active == 0:
                    ratio = 0.0
                else:
                    for m in active:
                        busy_sessions = m.is_busy_in_shift(day_code, start_p, end_p)
                        if busy_sessions:
                            for s in busy_sessions:
                                busy_details.append({
                                    "member": m.name,
                                    "member_id": m.id,
                                    "color": m.color_hex,
                                    "course": s.course_name,
                                    "room": s.room or "Chưa rõ phòng",
                                    "periods": f"Tiết {s.start_period}-{s.end_period}",
                                })
                        else:
                            free_members.append(m.name)

                    ratio = len(free_members) / total_active

                matrix[day_code][shift_id] = ShiftAvailability(
                    day_code=day_code,
                    day_name=day_name,
                    shift_id=shift_id,
                    shift_name=shift_name,
                    time_range=time_range,
                    start_period=start_p,
                    end_period=end_p,
                    total_active_members=total_active,
                    free_count=len(free_members),
                    busy_count=len(busy_details),
                    ratio=ratio,
                    free_members=free_members,
                    busy_details=busy_details,
                )

        return matrix

    def compute_period_matrix(self) -> Dict[str, Dict[int, Dict[str, Any]]]:
        """
        Computes detailed availability for each of the 15 individual periods across 7 days.
        """
        active = self.active_members
        total_active = len(active)
        matrix: Dict[str, Dict[int, Dict[str, Any]]] = {}

        for day_code, day_name, date_str in DAYS:
            matrix[day_code] = {}
            for p_id, (t_start, t_end, shift, ca) in TDTU_PERIODS.items():
                busy_list = []
                free_list = []

                for m in active:
                    session = m.is_busy_in_period(day_code, p_id)
                    if session:
                        busy_list.append({
                            "member": m.name,
                            "member_id": m.id,
                            "course": session.course_name,
                            "room": session.room,
                        })
                    else:
                        free_list.append(m.name)

                ratio = (len(free_list) / total_active) if total_active > 0 else 0.0
                matrix[day_code][p_id] = {
                    "time": f"{t_start} - {t_end}",
                    "shift": shift,
                    "ca": ca,
                    "free_count": len(free_list),
                    "busy_count": len(busy_list),
                    "ratio": ratio,
                    "free_members": free_list,
                    "busy_details": busy_list,
                }

        return matrix

    def find_golden_windows(self, min_ratio: float = 0.8) -> List[GoldenWindow]:
        """
        Scans for continuous free periods matching or exceeding min_ratio (e.g. 1.0 or 0.8).
        """
        active = self.active_members
        total_active = len(active)
        if total_active == 0:
            return []

        period_matrix = self.compute_period_matrix()
        windows: List[GoldenWindow] = []

        for day_code, day_name, date_str in DAYS:
            day_data = period_matrix[day_code]
            current_window: Optional[Dict[str, Any]] = None

            for p_id in sorted(day_data.keys()):
                p_info = day_data[p_id]
                if p_info["ratio"] >= min_ratio:
                    if current_window is None:
                        current_window = {
                            "day_code": day_code,
                            "day_name": day_name,
                            "date": date_str,
                            "start_period": p_id,
                            "end_period": p_id,
                            "free_members_set": set(p_info["free_members"]),
                            "busy_members_set": {b["member"] for b in p_info["busy_details"]},
                            "min_ratio_seen": p_info["ratio"],
                            "min_free_seen": p_info["free_count"],
                        }
                    else:
                        current_window["end_period"] = p_id
                        current_window["free_members_set"] &= set(p_info["free_members"])
                        current_window["busy_members_set"] |= {b["member"] for b in p_info["busy_details"]}
                        current_window["min_ratio_seen"] = min(current_window["min_ratio_seen"], p_info["ratio"])
                        current_window["min_free_seen"] = min(current_window["min_free_seen"], p_info["free_count"])
                else:
                    if current_window:
                        windows.append(self._build_golden_window(current_window, total_active))
                        current_window = None

            if current_window:
                windows.append(self._build_golden_window(current_window, total_active))

        return windows

    def _build_golden_window(self, w_data: dict, total_active: int) -> GoldenWindow:
        start_p = w_data["start_period"]
        end_p = w_data["end_period"]
        t_start = TDTU_PERIODS[start_p][0]
        t_end = TDTU_PERIODS[end_p][1]
        time_range = f"{t_start} - {t_end}"

        free_m = sorted(list(w_data["free_members_set"]))
        busy_m = sorted(list(w_data["busy_members_set"]))

        return GoldenWindow(
            day_code=w_data["day_code"],
            day_name=w_data["day_name"],
            date=w_data["date"],
            start_period=start_p,
            end_period=end_p,
            time_range=time_range,
            ratio=w_data["min_ratio_seen"],
            free_count=w_data["min_free_seen"],
            total_count=total_active,
            free_members=free_m,
            busy_members=busy_m,
        )

    def generate_ics_content(self, min_ratio: float = 0.8) -> str:
        """
        Generates standard RFC 5545 iCalendar content for all golden windows.
        """
        windows = self.find_golden_windows(min_ratio=min_ratio)
        total_active = len(self.active_members)

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//rat Timetable Compositor//VN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Lịch Trống Chung CLB",
            "X-WR-TIMEZONE:Asia/Ho_Chi_Minh",
        ]

        now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        for idx, w in enumerate(windows):
            start_time_str = TDTU_PERIODS[w.start_period][0]
            end_time_str = TDTU_PERIODS[w.end_period][1]

            dt_date = w.date.replace("-", "")
            dt_start = f"{dt_date}T{start_time_str.replace(':', '')}00"
            dt_end = f"{dt_date}T{end_time_str.replace(':', '')}00"

            badge = "100% RẢNH" if w.free_count == total_active else f"{w.free_count}/{total_active} Rảnh"
            title = f"[CLB FREE] {w.day_name}: Tiết {w.start_period}-{w.end_period} ({badge})"
            
            free_str = ", ".join(w.free_members) if w.free_members else "Không có"
            busy_str = f"\\nBận: {', '.join(w.busy_members)}" if w.busy_members else ""
            desc = f"Khung giờ rảnh sinh hoạt / họp CLB.\\nRảnh ({w.free_count}/{total_active}): {free_str}{busy_str}\\nThời gian: {start_time_str} - {end_time_str}"

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:rat-club-{dt_start}-{idx}@rat.local",
                f"DTSTAMP:{now_utc}",
                f"DTSTART;TZID=Asia/Ho_Chi_Minh:{dt_start}",
                f"DTEND;TZID=Asia/Ho_Chi_Minh:{dt_end}",
                f"SUMMARY:{title}",
                f"DESCRIPTION:{desc}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    def generate_chat_message(self) -> str:
        """
        Generates a beautifully formatted, aesthetic Zalo / Messenger announcement message.
        """
        active = self.active_members
        total = len(active)
        if total == 0:
            return "⚠️ Chưa có thành viên nào được kích hoạt để tính lịch."

        windows_100 = self.find_golden_windows(min_ratio=1.0)
        windows_80 = [w for w in self.find_golden_windows(min_ratio=0.8) if w.free_count < total]

        names_str = ", ".join([m.name for m in active])

        lines = [
            "🍵 **LỊCH TRỐNG CHUNG CLB — KHUNG GIỜ VÀNG** 🍵",
            f"👥 **Thành viên tham gia ({total} bạn):** {names_str}",
            "━" * 28,
        ]

        if windows_100:
            lines.append("✨ **KHUNG GIỜ VÀNG (100% CẢ NHÓM ĐỀU RẢNH):**")
            for idx, w in enumerate(windows_100, 1):
                span = w.span_periods
                lines.append(f"  {idx}. 🌿 **{w.day_name}**: Tiết {w.start_period} ➔ {w.end_period} ({w.time_range}) • {span} tiết liền mạch")
        else:
            lines.append("🌿 *Không có khung giờ nào 100% rảnh trong tuần này.*")

        lines.append("")

        if windows_80:
            lines.append(f"☀️ **KHUNG GIỜ KHẢ DỤNG CAO (≥80% RẢNH, {total-1}/{total} BẠN):**")
            for idx, w in enumerate(windows_80, 1):
                busy_str = f" *(Kẹt: {', '.join(w.busy_members)})*" if w.busy_members else ""
                lines.append(f"  {idx}. ☀️ **{w.day_name}**: Tiết {w.start_period} ➔ {w.end_period} ({w.time_range}) • {w.free_count}/{total} bạn rảnh{busy_str}")

        lines.extend([
            "",
            "━" * 28,
            "💡 *Được tính toán và đồng bộ tự động từ rat Timetable Compositor.*",
        ])

        return "\n".join(lines)
