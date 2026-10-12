from django import template

register = template.Library()

THAI_DAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']
THAI_MONTHS = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
               'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
THAI_MONTHS_SHORT = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                    'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']

@register.filter # ทำให้ใช้ {{d|thai_date}} ใน template ได้
def thai_date(value, style='full'):
    if not value:
        return ''
    year = value.year + 543  # ค.ศ. --> พ.ศ.
    if style == 'short':
        return f"{value.day} {THAI_MONTHS_SHORT[value.month - 1]} {year}" # list เริ่มที่ 0 จึงต้องลบ 1
    text = f"{value.day} {THAI_MONTHS[value.month - 1]} {year}"
    if style == 'long':
        return text
    return f"วัน{THAI_DAYS[value.weekday()]}ที่ {text}"