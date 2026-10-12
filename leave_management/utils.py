from datetime import timedelta
from .models import Holiday

def get_holiday_dates(start, end):
    return set(Holiday.objects.filter(date__range=(start, end)).values_list('date', flat=True))

def leave_days(start, end, holidays=None):
    if end < start:
        return 0
    if holidays is None:
        holidays = get_holiday_dates(start, end)
    total = 0
    day = start
    while day <= end:
        if day.weekday() < 5 and day not in holidays:  # จันทร์-ศุกร์ และไม่ใช่วันหยุด
            total += 1
        day += timedelta(days=1)
    return total