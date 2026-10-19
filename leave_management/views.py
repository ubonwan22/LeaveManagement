from datetime import date
from urllib.parse import quote_plus

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.db import transaction
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
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


def _paginate(request, qs, per_page=10):
    """แบ่งหน้า (หน้าละ 10 รายการ) คืน (page_obj, paginator, page_numbers)"""
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_numbers = [
        n if n != paginator.ELLIPSIS else '…'
        for n in paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)]
    return page_obj, paginator, page_numbers


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


class AppLoginView(auth_views.LoginView):
    """ล็อกอินสำเร็จแล้วแสดงป๊อปอัพต้อนรับ"""

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        emp = get_employee(user)
        name = emp.name if emp else user.get_full_name() or user.username
        messages.success(self.request, f'เข้าสู่ระบบสำเร็จ ยินดีต้อนรับ {name}')
        return response


class AppLogoutView(auth_views.LogoutView):
    """ล็อกเอาต์แล้วแสดงป๊อปอัพที่หน้าล็อกอิน"""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, 'ออกจากระบบเรียบร้อยแล้ว')
        return response


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
    my_employee = None if request.user.is_superuser else get_employee(request.user)
    approver = is_approver(request.user)
    return render(request, 'leave_management/dashboard.html', {
        'my_employee': my_employee,  # วันลาคงเหลือของตัวเอง (admin ไม่มี)
        'cols': 3 + (1 if approver else 0) + (1 if my_employee else 0),  # จำนวนการ์ด ใช้จัดคอลัมน์
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
    page_obj, paginator, page_numbers = _paginate(request, qs)
    items = _with_days(page_obj.object_list)
    for r in items:  # ปุ่มอนุมัติ/ไม่อนุมัติโชว์เฉพาะคนที่มีสิทธิ์ตัดสินใบลานั้น
        r.can_decide = r.status == S.PENDING and can_decide(request.user, r)
    return render(request, 'leave_management/request_list.html', {
        'requests': items,
        'tabs': tabs,
        'current': current,
        'page_obj': page_obj, 'paginator': paginator, 'page_numbers': page_numbers,
        'extra': f'&status={current}' if current in S.values else '',  # คงตัวกรองสถานะตอนเปลี่ยนหน้า
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
    page_obj, paginator, page_numbers = _paginate(request, qs)
    return render(request, 'leave_management/employee_list.html', {
        'employees': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'page_numbers': page_numbers, 'q': q,
        'extra': f'&q={quote_plus(q)}' if q else '',  # คงคำค้นหาตอนเปลี่ยนหน้า
    })


def employee_detail(request, pk):
    """ประวัติการลาของพนักงานรายคน (เฉพาะแอดมิน)"""
    if not request.user.is_superuser:
        raise PermissionDenied
    emp = get_object_or_404(Employee.objects.select_related('manager'), pk=pk)
    history = _with_days(emp.leave_requests.select_related('leave_type').order_by('-start_date', '-id'))
    S = LeaveRequest.Status
    return render(request, 'leave_management/employee_detail.html', {
        'emp': emp,
        'history': history,
        'total': len(history),
        'pending': sum(1 for r in history if r.status == S.PENDING),
        'approved': sum(1 for r in history if r.status == S.APPROVED),
        'approved_days': sum(r.days for r in history if r.status == S.APPROVED),
    })


def holiday_list(request):
    year = date.today().year
    return render(request, 'leave_management/holiday_list.html', {
        'holidays': Holiday.objects.filter(date__year=year).order_by('date'),
        'year_be': year + 543,
        'today': date.today(),
    })