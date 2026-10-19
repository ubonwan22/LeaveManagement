# Mock data generator สำหรับสร้างพนักงานปลอมและวันหยุดนักขัตฤกษ์
import random
from datetime import date

import holidays
from faker import Faker
from django.contrib.auth import get_user_model
from django.db import connection
from django.core.management.base import BaseCommand

from leave_management.accounts import create_users_for_employees, DEFAULT_PASSWORD
from leave_management.models import Employee, LeaveType, LeaveRequest, Holiday

POSITIONS = [
    'นักพัฒนาระบบ', 'นักวิเคราะห์ระบบ', 'นักออกแบบ UX/UI', 'เจ้าหน้าที่บัญชี', 
    'เจ้าหน้าที่ HR', 'ผู้ดูแลระบบเครือข่าย', 'นักวิเคราะห์ข้อมูล'
]
MANAGER_POSITIONS = ['หัวหน้าทีมพัฒนา', 'ผู้จัดการฝ่าย', 'หัวหน้าฝ่ายบุคคล']

def reset_ids(*models):
    """รีเซ็ตค่า ID ของโมเดลที่ระบุ"""
    with connection.cursor() as cursor:
        for model in models:
            cursor.execute(f"ALTER TABLE `{model._meta.db_table}` AUTO_INCREMENT = 1")

class Command(BaseCommand):
    help = 'สร้างพนักงานปลอม 50 คน และวันหยุดนักขัตฤกษ์ของปีปัจจุบัน'

    def handle(self, *args, **kwargs):
        fake = Faker('th_TH')
        Faker.seed(42)  
        random.seed(42) 

        #ล้างข้อมูลจำลองเดิม เพื่อให้รันซ้ำโดยไม่เกิน 50 คน
        LeaveRequest.objects.all().delete()
        get_user_model().objects.filter(employee__isnull=False, is_superuser=False).delete()  # บัญชีของพนักงานจำลองเดิม
        Employee.objects.all().delete()
        Holiday.objects.all().delete()

        reset_ids(Employee, LeaveType, LeaveRequest, Holiday)

        #ประเภทการลา
        for name, day in [('ลาป่วย', 30), ('ลากิจ', 6), ('ลาพักร้อน', 10)]:
            LeaveType.objects.update_or_create(name=name, defaults={'max_days': day})

        #หัวหน้างาน 5 คน (ไม่มีหัวหน้าของตัวเอง)
        managers = [
            Employee.objects.create(
                name=fake.name(),
                position=random.choice(MANAGER_POSITIONS),
                leave_balance=random.randint(5, 15),
            ) 
            for _ in range(5)
        ]

        #พนักงาน 45 คน (มีหัวหน้า)
        for _ in range(45):
            Employee.objects.create(
                name=fake.name(),
                position=random.choice(POSITIONS),
                leave_balance=random.randint(0, 15),
                manager=random.choice(managers),
            )

        #วันหยุดนักขัตฤกษ์ของปีปัจจุบัน
        year = date.today().year
        for d, name in sorted(holidays.Thailand(years=year, language='th').items()):
            Holiday.objects.create(date=d, name=name)

        users = create_users_for_employees()  # สร้างบัญชีล็อกอิน emp<id> ให้พนักงานทุกคน

        self.stdout.write(self.style.SUCCESS(
            f'สร้างบัญชีล็อกอิน {users} บัญชี (username = emp<id>, รหัสผ่าน {DEFAULT_PASSWORD})\n'
            f'สร้างพนักงาน {Employee.objects.count()} คน, '
            f'วันหยุด {Holiday.objects.count()} วัน(ปี {year}) เรียบร้อย'))