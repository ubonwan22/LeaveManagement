from django import forms
from .models import Employee, LeaveRequest

INPUT = (
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 "
    "focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
)

def leave_days(start, end):
    """จำนวนวันลา (นับรวมวันเริ่มและวันสิ้นสุด)"""
    return (end - start).days + 1

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # กำหนดให้เลือกพนักงานได้เฉพาะพนักงานที่มี leave_balance > 0
        self.fields['employee'].queryset = Employee.objects.order_by('name')
        self.fields['employee'].empty_label = "--เลือกพนักงาน--"
        self.fields['leave_type'].empty_label = "--เลือกประเภทการลา--"

    def clean(self):
        data = super().clean()
        start, end, emp = data.get('start_date'), data.get('end_date'), data.get('employee')
        if start and end:
            if end < start:
                self.add_error('end_date', 'วันที่สิ้นสุดต้องไม่ก่อนวันที่เริ่มลา')
            elif emp:
                days = leave_days(start, end)
                if days > emp.leave_balance:
                    self.add_error(
                        'end_date',
                        f'วันลาคงเหลือของ {emp.name} มี {emp.leave_balance} วัน ไม่พอสำหรับลา {days} วัน',
                    )
        return data



