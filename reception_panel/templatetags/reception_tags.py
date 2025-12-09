# reception_panel/templatetags/reception_tags.py
from django import template
from django.utils import timezone
import jdatetime
from typing import Any

register = template.Library()

# نگاشت نام ماه‌ها
PERSIAN_MONTHS = {
    1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر', 5: 'مرداد', 6: 'شهریور',
    7: 'مهر', 8: 'آبان', 9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند'
}

# نگاشت روزهای هفته (0 = دوشنبه در استاندارد پایتون)
PERSIAN_WEEKDAYS = {
    0: 'دوشنبه', 1: 'سه‌شنبه', 2: 'چهارشنبه', 3: 'پنج‌شنبه', 
    4: 'جمعه', 5: 'شنبه', 6: 'یکشنبه'
}

def to_persian_digits(value):
    """تبدیل اعداد انگلیسی به فارسی"""
    persian_map = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    return "".join(persian_map.get(c, c) for c in str(value))

@register.filter(name='jalali_format')
def jalali_format(value: Any, format_string: str = '%Y/%m/%d') -> str:
    """
    فیلتر تبدیل تاریخ میلادی به شمسی با خروجی تضمینی فارسی.
    """
    if not value:
        return ''
    
    try:
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        
        j_date = jdatetime.datetime.fromgregorian(datetime=value)
        
        # --- مدیریت فرمت‌های خاص به صورت دستی ---
        
        # حالت ۱: نمایش کامل برای داشبورد (مثلاً: سه‌شنبه ۰۴ دی)
        # فرمت ورودی در تمپلیت: '%A %d %B'
        if '%A' in format_string and '%B' in format_string:
            weekday = PERSIAN_WEEKDAYS[j_date.weekday()]
            day = to_persian_digits(f"{j_date.day:02d}") # دو رقمی کردن روز
            month = PERSIAN_MONTHS[j_date.month]
            
            # ساخت خروجی: سه‌شنبه ۰۴ دی
            return f"{weekday} {day} {month}"
            
        # حالت ۲: فقط ساعت (مثلاً: ۱۴:۳۰)
        elif format_string == '%H:%M':
            time_str = j_date.strftime(format_string)
            return to_persian_digits(time_str)
            
        # حالت ۳: تاریخ استاندارد (۱۴۰۳/۰۹/۲۰)
        else:
            date_str = j_date.strftime(format_string)
            return to_persian_digits(date_str)
        
    except Exception as e:
        # در صورت بروز هرگونه خطا، مقدار اولیه را برگردان
        return str(value)