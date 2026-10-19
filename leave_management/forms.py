from django import forms
from .models import Employee, LeaveRequest
from .permissions import get_employee
from .utils import leave_days

INPUT = (
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 "
    "focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
)

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date']
        labels = {
            'employee': 'พนักงาน',
            'leave_type': 'ประเภทการลา',
            'start_date': 'วันที่เริ่มต้น',
            'end_date': 'วันที่สิ้นสุด',
        }
        widgets = {
            'employee': forms.Select(attrs={'class': INPUT}),
            'leave_type': forms.Select(attrs={'class': INPUT}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        employees = Employee.objects.order_by('name')
        self.fields['employee'].empty_label = "--เลือกพนักงาน--"
        self.fields['leave_type'].empty_label = "--เลือกประเภทการลา--"
        # ผู้ใช้ทั่วไป (ไม่ใช่แอดมิน) ยื่นใบลาได้เฉพาะของตัวเอง -> ล็อกช่องพนักงานเป็นตัวเอง
        if user is not None and not user.is_superuser:
            me = get_employee(user)
            employees = employees.filter(pk=me.pk) if me else employees.none()
            if me:
                self.fields['employee'].empty_label = None
                self.fields['employee'].disabled = True
                self.initial['employee'] = me.pk
        self.fields['employee'].queryset = employees

    def clean(self):
        data = super().clean()
        start, end, emp = data.get('start_date'), data.get('end_date'), data.get('employee')
        if start and end:
            if end < start:
                self.add_error('end_date', 'วันที่สิ้นสุดต้องไม่ก่อนวันที่เริ่มลา')
            elif emp:
                days = leave_days(start, end)
                if days == 0:
                    self.add_error(
                        'end_date',
                        'ช่วงวันที่เลือกเป็นวันเสาร์-อาทิตย์หรือวันหยุดนักขัตฤกษ์ทั้งหมด ไม่ต้องยื่นใบลา',
                    )
                elif days > emp.leave_balance:
                    self.add_error(
                        'end_date',
                        f'วันลาคงเหลือของ {emp.name} มี {emp.leave_balance} วัน ไม่พอสำหรับลา {days} วัน',
                    )
        return data