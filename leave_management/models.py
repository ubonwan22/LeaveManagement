from django.conf import settings
from django.db import models

# โครงสร้างตาราง
class Employee(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True) #ตำแหน่งงาน
    leave_balance = models.PositiveIntegerField(default=10) # จำนวนวันลาที่เหลือ
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates') #หัวหน้างาน
    # บัญชีล็อกอินของพนักงานคนนี้ (ใช้แยกสิทธิ์ว่าใครเป็นหัวหน้า/ลูกน้อง)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee')

    @property
    def is_manager(self):
        """เป็นหัวหน้า = มีลูกน้องอย่างน้อย 1 คน"""
        return self.subordinates.exists()

    def __str__(self):
        return self.name

class LeaveType(models.Model):
    """ประเภทลา: ลาป่วย, ลากิจ, ลาพักร้อน"""
    name = models.CharField(max_length=100)
    max_days = models.PositiveIntegerField(default=0) # จำนวนวันลาที่อนุญาตสูงสุด

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'รอดำเนินการ'
        APPROVED = 'APPROVED', 'อนุมัติ'
        REJECTED = 'REJECTED', 'ไม่อนุมัติ'

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='leave_requests') #พนักงานที่ขอลา
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE) #ประเภทการลา
    start_date = models.DateField() #วันเริ่มลา
    end_date = models.DateField() #วันสิ้นสุดการลา
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING) #สถานะการลา

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

class Holiday(models.Model):
    """วันหยุดราชการ"""
    date = models.DateField(unique=True) #วันที่หยุด
    name = models.CharField(max_length=200) #ชื่อวันหยุด

    def __str__(self):
        return f"{self.date} ({self.name})"