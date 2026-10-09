# LeaveManagement ระบบลางานออนไลน์

**โครงสร้าง Projects**
LeaveManagement/
├── manage.py                 # ตัวสั่งงานหลักของ Django (runserver, migrate ฯลฯ)
├── .env                      # ค่าลับ เช่น รหัสผ่านฐานข้อมูล (ไม่ push ขึ้น GitHub)
├── .gitignore                # รายการไฟล์ที่ Git ไม่ต้องติดตาม
├── requirements.txt          # รายการ Library ที่ต้องติดตั้ง
├── README.md                 # ไฟล์นี้
├── venv/                     # Virtual Environment (ไม่ push ขึ้น GitHub)
│
├── office_system/            # โฟลเดอร์ตั้งค่าของ Project
│   ├── __init__.py           # ตั้งค่า PyMySQL ให้ Django ใช้แทน mysqlclient
│   ├── settings.py           # ตั้งค่า DATABASES, INSTALLED_APPS, อ่านค่าจาก .env
│   ├── urls.py               # ตาราง URL หลัก (include ไปยัง leave_management)
│   ├── asgi.py
│   └── wsgi.py
│
└── leave_management/         # App หลักของระบบลางาน
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py             # โครงสร้างตาราง (Employee)
    ├── views.py              # ตรรกะหน้าเว็บ (ดึงชื่อพนักงานจาก MySQL)
    ├── urls.py               # URL ของ App นี้
    ├── tests.py
    └── migrations/           # ไฟล์ migration ที่ Django สร้างให้

**วิธีติดตั้งและรัน**
1. เตรียมสิ่งที่ต้องมี
- Python (ติ๊ก Add Python to PATH ตอนติดตั้ง)
- MySQL Server 8.0 และ MySQL Workbench
- Git

2. สร้างและเปิดใช้ Virtual Environment
# สร้าง venv
python -m venv venv

# เปิดใช้งาน (Windows PowerShell)
venv\Scripts\activate

# เปิดใช้งาน (Windows cmd)
venv\Scripts\activate.bat

# เปิดใช้งาน (Mac/Linux)
source venv/bin/activate

3. ติดตั้ง Library
pip install -r requirements.txt

หรือติดตั้งเอง
pip install "django>=5.2,<5.3" pymysql cryptography python-dotenv
**หมายเหตุ:** Django 6 ขึ้นไปต้องใช้ MySQL 8.4+ ถ้าใช้ MySQL 8.0 ให้ใช้ Django 5.2 LTS

4. สร้างฐานข้อมูลและ User ใน MySQL
ปิด MySQL Workbench ล็อกอินด้วย root แล้วรันใน Query Tab
CREATE DATABASE IF NOT EXISTS leave_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY '<รหัสผ่านของคุณ>';
GRANT ALL PRIVILEGES ON leave_db.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;

ไม่ต้องสร้างตารางเอง Django จะสร้างให้ผ่าน migration

5. ตั้งค่าไฟล์ .env

คัดลอก .env.example เป็น .env แล้วกรอกค่า

DB_NAME=leave_db
DB_USER=admin
DB_PASSWORD=<รหัสผ่านที่ตั้งในขั้นที่ 5>
DB_HOST=127.0.0.1
DB_PORT=3306

- ไม่ต้องใส่เครื่องหมายคำพูด (ยกเว้นรหัสผ่านที่มีอักขระพิเศษ เช่น `#`)
- ไม่มีช่องว่างรอบเครื่องหมาย `=`
- ไฟล์ .env ต้องอยู่โฟลเดอร์เดียวกับ manage.py

6. สร้างตารางในฐานข้อมูล

powershell
python manage.py makemigrations leave_management
python manage.py migrate

7. เพิ่มข้อมูลจำลอง (Mock Data)

powershell
python manage.py shell

python
from leave_management.models import Employee
Employee.objects.create(name="สมชาย ใจดี")
exit()

8. รัน Server

powershell
python manage.py runserver

เปิดเบราว์เซอร์ไปที่ <http://127.0.0.1:8000/> จะเห็นข้อความ

Hello, สมชาย ใจดี

โดยชื่อดึงมาจากตาราง leave_management_employee ใน MySQL

## คำสั่งที่ใช้บ่อย

| คำสั่ง | ทำอะไร |
|---|---|
| python manage.py runserver | รันเซิร์ฟเวอร์พัฒนา |
| python manage.py makemigrations | สร้างไฟล์ migration จากการแก้ models.py |
| python manage.py migrate | สั่งให้ฐานข้อมูลเปลี่ยนตาม migration |
| python manage.py shell | เปิด Python shell ของ Django |
| python manage.py createsuperuser | สร้างผู้ดูแลระบบสำหรับ /admin/ |
| pip freeze > requirements.txt | บันทึกรายการ Library ปัจจุบัน |
| deactivate | ปิด Virtual Environment |

## ใช้งานร่วมกับ Git / GitHub

bash
git add .
git commit -m "ข้อความอธิบายการเปลี่ยนแปลง"
git push
git pull        # ดึงงานล่าสุดจาก GitHub

ตรวจว่า .gitignore มีรายการเหล่านี้เสมอ เพื่อไม่ให้ไฟล์สำคัญหลุดขึ้น GitHub

venv/
__pycache__/
*.pyc
db.sqlite3
.env
