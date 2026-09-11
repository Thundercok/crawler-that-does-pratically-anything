"""
tests/test_timetable_compositor.py — Unit & UI Tests for Club Timetable Compositor.
Validates multi-member schedule fusion, golden window extraction, iCalendar generation,
and PyQt6 Chill UI responsiveness.
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from rat.timetable.compositor import TimetableCompositor, availability_to_color
from rat.timetable.data import get_default_club_members
from rat.timetable.model import DAYS, SHIFTS, TDTU_PERIODS, ClassSession, MemberSchedule
from rat.ui.schedule_window import ScheduleCompositorWindow


class TestTimetableCompositorEngine(unittest.TestCase):
    def setUp(self):
        self.members = get_default_club_members()
        self.compositor = TimetableCompositor(self.members)

    def test_members_loaded(self):
        self.assertEqual(len(self.members), 6)
        names = [m.name for m in self.members]
        self.assertIn("Huỳnh Nhật Huy", names)
        self.assertIn("Thông Ngọc Lan Anh", names)
        self.assertIn("Phạm Vũ Thảo Nguyên", names)

    def test_shift_matrix_calculation(self):
        matrix = self.compositor.compute_shift_matrix()
        self.assertIn("T2", matrix)
        self.assertIn("ca1", matrix["T2"])
        
        ca1_t2 = matrix["T2"]["ca1"]
        self.assertEqual(ca1_t2.shift_id, "ca1")
        self.assertEqual(ca1_t2.start_period, 1)
        self.assertEqual(ca1_t2.end_period, 3)
        self.assertEqual(ca1_t2.total_active_members, 6)
        # Several members have classes on Monday morning (Tiết 1-3)
        self.assertTrue(ca1_t2.busy_count > 0)
        self.assertTrue(len(ca1_t2.free_members) < 6)

    def test_find_golden_windows(self):
        windows_100 = self.compositor.find_golden_windows(min_ratio=1.0)
        self.assertGreater(len(windows_100), 0)
        
        # Tuesday evening (Tiết 13-15) and Sunday should be in golden windows
        day_codes = [w.day_code for w in windows_100]
        self.assertIn("CN", day_codes)
        
        for w in windows_100:
            self.assertEqual(w.ratio, 1.0)
            self.assertEqual(w.free_count, 6)
            self.assertEqual(len(w.busy_members), 0)

    def test_toggle_member(self):
        # Initial active
        self.assertEqual(len(self.compositor.active_members), 6)
        
        # Toggle Huy off
        res = self.compositor.toggle_member("m1")
        self.assertFalse(res)
        self.assertEqual(len(self.compositor.active_members), 5)
        
        # Recalculate matrix
        matrix = self.compositor.compute_shift_matrix()
        self.assertEqual(matrix["T2"]["ca1"].total_active_members, 5)

    def test_ics_generation(self):
        ics = self.compositor.generate_ics_content(min_ratio=0.8)
        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("END:VCALENDAR", ics)
        self.assertIn("BEGIN:VEVENT", ics)
        self.assertIn("SUMMARY:[CLB FREE]", ics)
        self.assertIn("TZID=Asia/Ho_Chi_Minh", ics)

    def test_chat_message_generation(self):
        msg = self.compositor.generate_chat_message()
        self.assertIn("LỊCH TRỐNG CHUNG CLB", msg)
        self.assertIn("KHUNG GIỜ VÀNG", msg)
        self.assertIn("Huỳnh Nhật Huy", msg)

    def test_availability_to_color_palette(self):
        c100 = availability_to_color(1.0)
        self.assertEqual(c100["badge"], "🌿 100%")
        self.assertEqual(c100["bg"], "#dcfce7")

        c80 = availability_to_color(0.83)
        self.assertEqual(c80["badge"], "☀️ Đa số")

        c50 = availability_to_color(0.5)
        self.assertEqual(c50["badge"], "✨ Một nửa")

        c0 = availability_to_color(0.2)
        self.assertEqual(c0["badge"], "🌧️ Kẹt lịch")


class TestScheduleCompositorWindowUI(unittest.TestCase):
    def setUp(self):
        self.window = ScheduleCompositorWindow()
        self.window._select_all_members()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        app.processEvents()

    def test_ui_initialization(self):
        self.assertIn("Ghép Lịch & Khung Giờ Vàng CLB", self.window.windowTitle())
        self.assertEqual(self.window.compositor.active_members.__len__(), 6)
        # 8 columns (1 header + 7 days) * 6 rows (1 header + 5 shifts) = 48 items in grid
        self.assertEqual(self.window.grid_layout.count(), 48)

    def test_toggle_member_chip(self):
        self.window._on_toggle_member("m1")
        app.processEvents()
        self.assertEqual(len(self.window.compositor.active_members), 5)
        self.assertIn("5/6", self.window.stats_pill.text())

    def test_select_and_clear_all_members(self):
        self.window._clear_all_members()
        app.processEvents()
        self.assertEqual(len(self.window.compositor.active_members), 0)

        self.window._select_all_members()
        app.processEvents()
        self.assertEqual(len(self.window.compositor.active_members), 6)

    def test_cell_click_renders_details(self):
        shift_matrix = self.window.compositor.compute_shift_matrix()
        test_shift = shift_matrix["T2"]["ca1"]
        self.window._on_cell_clicked(test_shift)
        app.processEvents()
        
        self.assertIn("Thứ 2", self.window.detail_title.text())
        self.assertIn("Ca 1", self.window.detail_title.text())


if __name__ == "__main__":
    unittest.main()
