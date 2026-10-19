#!/bin/sh
set -e

echo ">> migrate"
python manage.py migrate --noinput

# ใส่ข้อมูลจำลองเฉพาะตอนฐานข้อมูลยังว่าง (seed_data ล้างข้อมูลเดิมทิ้งทุกครั้งที่รัน จึงไม่รันซ้ำอัตโนมัติ)
if [ "${SEED_DATA:-1}" = "1" ]; then
  COUNT=$(python manage.py shell -c "from leave_management.models import Employee; print(Employee.objects.count())" | tail -n 1)
  if [ "$COUNT" = "0" ]; then
    echo ">> seed_data"
    python manage.py seed_data
  fi
fi

# สร้างบัญชีล็อกอิน (emp<id>) ให้พนักงานที่ยังไม่มีบัญชี (รันซ้ำได้ ไม่ทับของเดิม)
python manage.py create_employee_users

# สร้าง superuser ครั้งแรกจากค่าใน .env (ถ้ามีอยู่แล้วจะข้าม)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" 2>/dev/null \
    && echo ">> created superuser $DJANGO_SUPERUSER_USERNAME" || true
fi

exec "$@"
