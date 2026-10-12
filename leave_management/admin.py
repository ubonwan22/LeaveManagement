from django.contrib import admin
from .models import Employee, Holiday, LeaveRequest, LeaveType

# Register your models here.
#ไว้กรอกข้อมูลโมดูล เพื่อจัดการข้อมูลผ่านหน้า /admin/
@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name','max_days')

#ลงวทะเบียน model ให้โผล่ใน /admin/
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'position', 'leave_balance', 'manager') # column ในตาราง
    list_filter = ('position',) #ตัวกรองด้านขวา (ต้องมี , ต่อท้าย เพราะมีแค่ตัวเดียว)
    search_fields = ('name', 'position') #ช่องค้นหา
    list_per_page = 50 

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name')
    list_filter = ('date',)
