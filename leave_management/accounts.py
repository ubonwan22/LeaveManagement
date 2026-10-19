import re

from django.contrib.auth import get_user_model

from .models import Employee

DEFAULT_PASSWORD = 'leave1234'  # รหัสผ่านตั้งต้นสำหรับบัญชีจำลอง (ใช้เดโมเท่านั้น)


def create_users_for_employees():
    """สร้างบัญชีล็อกอินให้พนักงานที่ยังไม่มี user  (username = emp<id>, เช่น emp1)
    คืนจำนวนบัญชีที่สร้างใหม่"""
    User = get_user_model()
    created = 0
    for emp in Employee.objects.filter(user__isnull=True):
        username = f'emp{emp.pk}'
        user = User.objects.filter(username__iexact=username).first()  # ถ้ามีบัญชีชื่อนี้อยู่แล้ว (ตัวพิมพ์เล็ก/ใหญ่ไม่สน) ให้ผูกเลย
        if user is None:
            user = User(username=username, first_name=emp.name)
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            created += 1
        emp.user = user
        emp.save(update_fields=['user'])
    return created



def link_user_to_employee(user):
    """ผูกบัญชีชื่อ emp<id> (เช่น emp1, Emp1) กับพนักงานที่มี id นั้นอัตโนมัติ ถ้ายังไม่ได้ผูก
    คืน Employee ที่ผูกได้ หรือ None ถ้าไม่เข้าเงื่อนไข"""
    if not user.is_authenticated or user.is_superuser:
        return None
    match = re.fullmatch(r'emp(\d+)', user.username, re.IGNORECASE)
    if not match:
        return None
    emp = Employee.objects.filter(pk=int(match.group(1)), user__isnull=True).first()
    if emp is None:
        return None
    emp.user = user
    emp.save(update_fields=['user'])
    return emp