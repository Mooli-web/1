/* static/js/booking-calendar.js */
/**
 * مدیریت تقویم (FullCalendar).
 * این فایل تقویم را می‌سازد و رویدادهای کلیک روی روزها را مدیریت می‌کند.
 */

const BookingCalendar = {
    calendar: null,
    availableDatesMap: {}, // دیکشنری برای نگهداری روزهای دارای نوبت { '1402-08-10': [...] }

    init(calendarEl, onDateSelect) {
        if (!calendarEl) return;

        // اطمینان از لود شدن FullCalendar
        if (typeof FullCalendar === 'undefined') {
            console.error('FullCalendar library is not loaded.');
            return;
        }

        this.calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'fa', // زبان فارسی
            direction: 'rtl',
            headerToolbar: {
                left: 'prev,next',
                center: 'title',
                right: 'today'
            },
            // غیرفعال کردن انتخاب روزهای گذشته (اینجا فقط بصری، لاجیک اصلی در backend است)
            validRange: {
                start: new Date().toISOString().split('T')[0] // از امروز
            },
            
            dateClick: (info) => {
                // info.dateStr فرمت میلادی می‌دهد (مثلا 2023-11-01)
                // ما نیاز داریم این را به کلید شمسی تبدیل کنیم یا مستقیماً استفاده کنیم
                // بسته به خروجی API.
                
                // اما چون API ما کلید شمسی برمی‌گرداند (1402-08-10)، 
                // باید تبدیل تاریخ انجام شود یا از خاصیت‌های jalali-moment استفاده کنیم.
                
                // فرض: ما از روی کلاس‌های CSS یا اتریبیوت‌ها می‌فهمیم کدام روز فعال است
                // راه ساده‌تر: دریافت تاریخ میلادی کلیک شده و پیدا کردن معادلش در دیتای API
                
                if (typeof onDateSelect === 'function') {
                    onDateSelect(info.date, info.dateStr);
                }
            },

            /**
             * این تابع برای رنگ‌بندی روزها استفاده می‌شود
             */
            dayCellClassNames: (arg) => {
                // اگر برای این تاریخ اسلات خالی داشته باشیم، سبز شود
                // نکته: تبدیل تاریخ arg.date به فرمت کلید ما در availableDatesMap نیاز است
                
                // استفاده از jalali-moment برای تبدیل تاریخ سلول تقویم به شمسی
                const jDate = moment(arg.date).locale('fa').format('YYYY-MM-DD');
                
                if (this.availableDatesMap[jDate]) {
                    return ['fc-day-available'];
                }
                return ['fc-day-unavailable'];
            }
        });

        this.calendar.render();
    },

    /**
     * به‌روزرسانی داده‌های تقویم با اسلات‌های جدید
     * @param {Object} slotsData - دیکشنری {'1402-08-10': [...]}
     */
    updateEvents(slotsData) {
        if (!this.calendar) return;

        this.availableDatesMap = slotsData || {};
        // رندر مجدد برای اعمال کلاس‌های CSS جدید (سبز شدن روزهای خالی)
        this.calendar.render(); 
    }
};

window.BookingCalendar = BookingCalendar;