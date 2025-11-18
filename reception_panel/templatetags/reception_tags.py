from django import template
import jdatetime
from django.utils import timezone

register = template.Library()

@register.filter(name='jalali_format')
def jalali_format(value, format_string='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی با فرمت‌دهی صریح.
    استفاده: {{ value|jalali_format:"%Y/%m/%d %H:%M" }}
    """
    if not value:
        return ''
    
    try:
        # اطمینان از اینکه زمان محلی (ایران) است
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        
        # تبدیل به آبجکت شمسی
        j_date = jdatetime.datetime.fromgregorian(datetime=value)
        
        # فرمت‌دهی صریح به رشته (Bypass __str__)
        # تبدیل اعداد به فارسی برای زیبایی بیشتر
        formatted_date = j_date.strftime(format_string)
        
        persian_map = {
            '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
        }
        for eng, per in persian_map.items():
            formatted_date = formatted_date.replace(eng, per)
            
        return formatted_date
        
    except Exception as e:
        # در صورت بروز هرگونه خطا، مقدار اصلی را برگردان تا صفحه کرش نکند
        print(f"Jalali Conversion Error: {e}")
        return str(value)