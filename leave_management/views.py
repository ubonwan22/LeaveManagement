from datetime import date

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LeaveRequestForm
from .models import Employee, Holiday, LeaveRequest
from .permissions import (
    can_decide, decidable_requests, get_employee, is_approver,
    user_role, visible_employees, visible_requests,
)
from .utils import get_holiday_dates, leave_days


def hello(request):
    employee = Employee.objects.first()  # สร้าง SQL แล้วคืนพนักงานในแถวแรก
    if employee:
        return HttpResponse(f"Hello, {employee.name}")
    return HttpResponse("Hello, ไม่พบข้อมูลพนักงาน")


def _with_days(requests_):
    """แนบจำนวนวันลา (ไม่นับเสาร์-อาทิตย์/วันหยุด) ให้แต่ละใบลา เพื่อใช้แสดงผลใน template"""
    items = list(requests_)
    if items:
        # ดึงวันหยุดครั้งเดียวสำหรับทุกใบลา (ไม่ query ซ้ำทีละใบ)
        holidays = get_holiday_dates(
            min(r.start_date for r in items), max(r.end_date for r in items))
        for r in items:
            r.days = leave_days(r.start_date, r.end_date, holidays)
    return items


def dashboard(request):
    S = LeaveRequest.Status
    mine = visible_requests(request.user)  # ใบลาที่ผู้ใช้คนนี้มีสิทธิ์เห็น (หัวหน้า = เฉพาะทีมตัวเอง)
    counts = mine.aggregate(
        pending=Count('id', filter=Q(status=S.PENDING)),
        approved=Count('id', filter=Q(status=S.APPROVED)),
        rejected=Count('id', filter=Q(status=S.REJECTED)),
    )
    recent = mine.select_related('employee', 'leave_type').order_by('-id')[:5]
    upcoming = Holiday.objects.filter(date__gte=date.today()).order_by('date')[:5]

    # หน้าอนุมัติใบลา: เฉพาะหัวหน้า/แอดมินเท่านั้นที่เห็น
    pending = None
    if is_approver(request.user):
        pending = _with_days(
            decidable_requests(request.user).filter(status=S.PENDING)
            .select_related('employee', 'leave_type').order_by('id'))
    return render(request, 'leave_management/dashboard.html', {
        'employee_count': visible_employees(request.user).count(),
        'counts': counts,
        'recent': _with_days(recent),
        'upcoming': upcoming,
        'pending': pending,
        'role': user_role(request.user),
    })


def request_list(request):
    S = LeaveRequest.Status
    current = request.GET.get('status', '')
    mine = visible_requests(request.user)  # เห็นเฉพาะใบลาในขอบเขตของตัวเอง
    qs = mine.select_related('employee', 'leave_type').order_by('-id')
    if current in S.values:
        qs = qs.filter(status=current)
    totals = mine.aggregate(
        all=Count('id'),
        PENDING=Count('id', filter=Q(status=S.PENDING)),
        APPROVED=Count('id', filter=Q(status=S.APPROVED)),
        REJECTED=Count('id', filter=Q(status=S.REJECTED)),
    )
    tabs = [('', 'ทั้งหมด', totals['all'])] + [
        (value, label, totals[value]) for value, label in S.choices
    ]
    items = _with_days(qs)
    for r in items:  # ปุ่มอนุมัติ/ไม่อนุมัติโชว์เฉพาะคนที่มีสิทธิ์ตัดสินใบลานั้น
        r.can_decide = r.status == S.PENDING and can_decide(request.user, r)
    return render(request, 'leave_management/request_list.html', {
        'requests': items,
        'tabs': tabs,
        'current': current,
    })


def request_create(request):
    if not request.user.is_superuser and get_employee(request.user) is None:
        messages.error(request, 'บัญชีนี้ยังไม่ได้ผูกกับพนักงาน จึงยื่นใบลาไม่ได้ (ให้แอดมินผูกบัญชีที่หน้า Admin > Employees ช่อง User)')
        return redirect('dashboard')
    form = LeaveRequestForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        leave = form.save()
        days = leave_days(leave.start_date, leave.end_date)  # Total Days
        messages.success(
            request,
            f'ยื่นใบลาเรียบร้อย รวม {days} วัน (ไม่นับเสาร์-อาทิตย์และวันหยุดนักขัตฤกษ์) รอการอนุมัติ')
        return redirect('request_list')
    holidays = {d.isoformat(): name for d, name in Holiday.objects.values_list('date', 'name')}
    return render(request, 'leave_management/request_form.html', {'form': form, 'holidays': holidays})


@require_POST
def request_decide(request, pk):
    leave = get_object_or_404(visible_requests(request.user).select_related('employee'), pk=pk)
    if not can_decide(request.user, leave):
        raise PermissionDenied  # ลูกน้อง/คนนอกทีม อนุมัติหรือไม่อนุมัติไม่ได้ (403)
    action = request.POST.get('action')
    S = LeaveRequest.Status

    if leave.status != S.PENDING:
        messages.warning(request, 'ใบลานี้ถูกพิจารณาไปแล้ว')
    elif action == 'approve':
        days = leave_days(leave.start_date, leave.end_date)
        with transaction.atomic():
            emp = Employee.objects.select_for_update().get(pk=leave.employee_id)
            if emp.leave_balance < days:
                messages.error(request, f'วันลาคงเหลือของ {emp.name} ไม่พอ (เหลือ {emp.leave_balance} วัน)')
            else:
                emp.leave_balance -= days  # หักวันลาเมื่ออนุมัติ
                emp.save(update_fields=['leave_balance'])
                leave.status = S.APPROVED
                leave.save(update_fields=['status'])
                messages.success(request, f'อนุมัติใบลาของ {emp.name} แล้ว (หัก {days} วัน)')
    elif action == 'reject':
        leave.status = S.REJECTED
        leave.save(update_fields=['status'])
        messages.success(request, f'ไม่อนุมัติใบลาของ {leave.employee.name}')
    nxt = request.POST.get('next', '')  # กดจากหน้า dashboard ให้กลับไปหน้า dashboard
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        nxt = ''
    return redirect(nxt or 'request_list')


def employee_list(request):
    if not is_approver(request.user):
        raise PermissionDenied  # พนักงานทั่วไปเข้าหน้านี้ตรงๆ ไม่ได้
    q = request.GET.get('q', '').strip()
    qs = visible_employees(request.user).select_related('manager').order_by('id')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(position__icontains=q))
    return render(request, 'leave_management/employee_list.html', {'employees': qs, 'q': q})


def holiday_list(request):
    year = date.today().year
    return render(request, 'leave_management/holiday_list.html', {
        'holidays': Holiday.objects.filter(date__year=year).order_by('date'),
        'year_be': year + 543,
        'today': date.today(),
    })