from datetime import date

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import LeaveRequestForm, leave_days
from .models import Employee, Holiday, LeaveRequest


def hello(request):
    employee = Employee.objects.first()  # สร้าง SQL แล้วคืนพนักงานในแถวแรก
    if employee:
        return HttpResponse(f"Hello, {employee.name}")
    return HttpResponse("Hello, ไม่พบข้อมูลพนักงาน")


def _with_days(requests_):
    """แนบจำนวนวันลาให้แต่ละใบลา เพื่อใช้แสดงผลใน template"""
    items = list(requests_)
    for r in items:
        r.days = leave_days(r.start_date, r.end_date)
    return items


def dashboard(request):
    S = LeaveRequest.Status
    counts = LeaveRequest.objects.aggregate(
        pending=Count('id', filter=Q(status=S.PENDING)),
        approved=Count('id', filter=Q(status=S.APPROVED)),
        rejected=Count('id', filter=Q(status=S.REJECTED)),
    )
    recent = LeaveRequest.objects.select_related('employee', 'leave_type').order_by('-id')[:5]
    upcoming = Holiday.objects.filter(date__gte=date.today()).order_by('date')[:5]
    return render(request, 'leave_management/dashboard.html', {
        'employee_count': Employee.objects.count(),
        'counts': counts,
        'recent': _with_days(recent),
        'upcoming': upcoming,
    })


def request_list(request):
    S = LeaveRequest.Status
    current = request.GET.get('status', '')
    qs = LeaveRequest.objects.select_related('employee', 'leave_type').order_by('-id')
    if current in S.values:
        qs = qs.filter(status=current)
    totals = LeaveRequest.objects.aggregate(
        all=Count('id'),
        PENDING=Count('id', filter=Q(status=S.PENDING)),
        APPROVED=Count('id', filter=Q(status=S.APPROVED)),
        REJECTED=Count('id', filter=Q(status=S.REJECTED)),
    )
    tabs = [('', 'ทั้งหมด', totals['all'])] + [
        (value, label, totals[value]) for value, label in S.choices
    ]
    return render(request, 'leave_management/request_list.html', {
        'requests': _with_days(qs),
        'tabs': tabs,
        'current': current,
    })


def request_create(request):
    form = LeaveRequestForm(request.POST or None) # GET = ฟอร์มว่าง, POST = ฟอร์มที่กรอกข้อมูลแล้ว
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'ยื่นใบลาเรียบร้อย รอการอนุมัติ')
        return redirect('request_list') # ไปหน้ารายการใบลา
    return render(request, 'leave_management/request_form.html', {'form': form})


@require_POST
def request_decide(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
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
    return redirect('request_list')


def employee_list(request):
    q = request.GET.get('q', '').strip()
    qs = Employee.objects.select_related('manager').order_by('id')
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
