# reception_panel/templatetags/reception_tags.py
from django import template
from django.utils import timezone
import jdatetime
from typing import Any

register = template.Library()

@register.filter(name='jalali_format')
def jalali_format(value: Any, format_string: str = '%Y/%m/%d') -> str:
    """
    فیلتر تبدیل تاریخ میلادی به شمسی با اعداد فارسی.
    """
    if not value:
        return ''
    
    try:
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        
        j_date = jdatetime.datetime.fromgregorian(datetime=value)
        formatted_date = j_date.strftime(format_string)
        
        # تبدیل اعداد به فارسی
        persian_map = {
            '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
        }
        for eng, per in persian_map.items():
            formatted_date = formatted_date.replace(eng, per)
            
        return formatted_date
        
    except Exception:
        # در صورت خطا (مثلا مقدار ورودی تاریخ نیست)، همان مقدار را برگردان
        return str(value)