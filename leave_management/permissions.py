"""กฎสิทธิ์ของระบบลางาน
- แอดมิน (superuser): เห็นและอนุมัติได้ทุกอย่าง
- หัวหน้า (พนักงานที่มีลูกน้อง): เห็นข้อมูลตัวเอง + ลูกน้องในทีม และอนุมัติใบลาของลูกน้องได้
- ลูกน้อง: เห็นเฉพาะข้อมูลตัวเอง และอนุมัติ/ไม่อนุมัติไม่ได้
"""
from django.db.models import Q

from .accounts import link_user_to_employee
from .models import Employee, LeaveRequest


def get_employee(user):
    """คืน Employee ที่ผูกกับ user (ถ้าไม่มีคืน None)"""
    if not user.is_authenticated:
        return None
    emp = getattr(user, 'employee', None)
    if emp is None:
        emp = link_user_to_employee(user)  # ยังไม่ได้ผูก: ลองผูกให้อัตโนมัติจากชื่อ emp<id>
    return emp


def user_role(user):
    if user.is_superuser:
        return 'ผู้ดูแลระบบ'
    me = get_employee(user)
    if me is None:
        return 'ไม่มีข้อมูลพนักงานที่ผูกกับบัญชีนี้'
    return 'หัวหน้า' if me.is_manager else 'พนักงาน'


def is_approver(user):
    """มีสิทธิ์เห็นหน้าอนุมัติใบลาหรือไม่"""
    if user.is_superuser:
        return True
    me = get_employee(user)
    return bool(me and me.is_manager)


def visible_employees(user):
    """พนักงานที่ user คนนี้มองเห็น"""
    qs = Employee.objects.all()
    if user.is_superuser:
        return qs
    me = get_employee(user)
    if me is None:
        return qs.none()
    if me.is_manager:
        return qs.filter(Q(pk=me.pk) | Q(manager=me))  # ตัวเอง + ลูกน้องในทีม
    return qs.filter(pk=me.pk)


def visible_requests(user):
    """ใบลาที่ user คนนี้มองเห็น"""
    return LeaveRequest.objects.filter(employee__in=visible_employees(user))


def decidable_requests(user):
    """ใบลาที่ user คนนี้มีสิทธิ์อนุมัติ/ไม่อนุมัติ (ใบลาของลูกน้องโดยตรง)"""
    qs = LeaveRequest.objects.all()
    if user.is_superuser:
        return qs
    me = get_employee(user)
    if me is not None and me.is_manager:
        return qs.filter(Q(employee__manager=me) | Q(employee=me))  # ลูกน้องโดยตรง + ตัวเอง (ตัวเองอนุมัติไม่ได้ แต่โชว์ให้เห็น)
    return qs.none()


def can_decide(user, leave):
    if user.is_superuser:
        return True
    me = get_employee(user)
    if me is None:
        return False
    if leave.employee.id == me.pk:
        return me.is_manager  # ตัวเองอนุมัติไม่ได้ แต่หัวหน้าตัวเองอนุมัติได้
    return bool(me and leave.employee.manager_id == me.pk)