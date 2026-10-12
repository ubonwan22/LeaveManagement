from datetime import date

from django.test import SimpleTestCase

from .utils import leave_days


class LeaveDaysTests(SimpleTestCase):
    """ทดสอบการคำนวณวันลา (ส่ง holidays เข้าไปเอง จึงไม่ต้องใช้ฐานข้อมูล)"""

    def test_friday_to_monday_is_2_days(self):
        # ศุกร์ 16 ต.ค. 2569(ค.ศ. 2026) ถึง จันทร์ 19 ต.ค. -> ตัดเสาร์-อาทิตย์ เหลือ 2 วัน
        self.assertEqual(leave_days(date(2026, 10, 16), date(2026, 10, 19), set()), 2)

    def test_weekend_only_is_0_days(self):
        self.assertEqual(leave_days(date(2026, 10, 17), date(2026, 10, 18), set()), 0)

    def test_holiday_is_excluded(self):
        # ศุกร์ 23 ต.ค. เป็นวันปิยมหาราช ถึงจันทร์ 26 ต.ค. -> เหลือ 1 วัน
        holidays = {date(2026, 10, 23)}
        self.assertEqual(leave_days(date(2026, 10, 23), date(2026, 10, 26), holidays), 1)

    def test_single_working_day(self):
        self.assertEqual(leave_days(date(2026, 10, 14), date(2026, 10, 14), set()), 1)

    def test_full_week(self):
        # จันทร์ถึงอาทิตย์ = 5 วันทำงาน
        self.assertEqual(leave_days(date(2026, 10, 12), date(2026, 10, 18), set()), 5)
