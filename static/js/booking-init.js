/* static/js/booking-init.js */
/**
 * نقطه شروع (Entry Point) اسکریپت‌های رزرو.
 * این فایل پس از لود شدن صفحه اجرا می‌شود و ماژول‌های دیگر را فراخوانی می‌کند.
 */

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Booking System Initializing...');

    // 1. دریافت تنظیمات اولیه از HTML (دیتا اتریبیوت‌ها)
    // این بهترین روش برای انتقال URL ها از جنگو به JS است
    const configEl = document.getElementById('booking-config');
    if (!configEl) {
        console.warn('Booking config element not found. Skipping initialization.');
        return;
    }

    const config = {
        slotsApiUrl: configEl.dataset.slotsApiUrl,
        discountApiUrl: configEl.dataset.discountApiUrl,
        csrfToken: configEl.dataset.csrfToken,
    };

    // 2. راه‌اندازی State
    BookingState.init();

    // 3. راه‌اندازی تقویم
    const calendarEl = document.getElementById('calendar');
    BookingCalendar.init(calendarEl, (dateObj, dateStr) => {
        // وقتی روی یک روز کلیک شد:
        
        // الف) تبدیل تاریخ میلادی سلول به شمسی (کلید دیکشنری)
        const jDate = moment(dateObj).locale('fa').format('YYYY-MM-DD');
        
        // ب) بررسی وجود اسلات
        const slots = BookingCalendar.availableDatesMap[jDate];
        
        if (slots) {
            BookingState.state.selectedDate = jDate;
            // پ) نمایش اسلات‌ها در UI
            BookingUI.renderSlots(slots, (selectedSlot) => {
                // وقتی روی ساعت کلیک شد
                BookingState.setSlot(selectedSlot.start);
                
                // پر کردن فیلد مخفی فرم برای ارسال به سرور
                const hiddenInput = document.getElementById('id_slot'); // نام فیلد در فرم جنگو
                if (hiddenInput) {
                    hiddenInput.value = selectedSlot.start;
                }
                console.log('Slot Selected:', selectedSlot.start);
            });
        } else {
            BookingUI.clearSlots();
            // alert('برای این تاریخ نوبتی موجود نیست.');
        }
    });

    // 4. گوش دادن به تغییرات سرویس (برای لود مجدد تقویم)
    const serviceSelect = document.getElementById('id_services'); // نام فیلد Select2 یا چک‌باکس
    const deviceSelect = document.getElementById('id_device');

    const reloadCalendarData = async () => {
        // دریافت ID سرویس‌های انتخاب شده
        // فرض: اگر Select2 باشد
        let selectedServices = [];
        if (serviceSelect) {
             selectedServices = Array.from(serviceSelect.selectedOptions).map(opt => opt.value);
        }
        
        // دریافت دستگاه (اگر وجود دارد)
        let selectedDevice = deviceSelect ? deviceSelect.value : null;

        if (selectedServices.length === 0) {
            BookingCalendar.updateEvents({});
            BookingUI.clearSlots();
            return;
        }

        BookingUI.toggleLoading(true);

        // فراخوانی API
        const data = await BookingAPI.fetchAvailableSlots(
            config.slotsApiUrl, 
            selectedServices, 
            selectedDevice
        );

        BookingUI.toggleLoading(false);

        if (data) {
            // آپدیت تقویم با داده‌های جدید (رنگ کردن روزهای سبز)
            BookingCalendar.updateEvents(data);
            BookingUI.clearSlots(); // پاک کردن اسلات‌های ساعت چون تقویم رفرش شده
        }
    };

    // اتصال ایونت‌ها
    if (serviceSelect) {
        serviceSelect.addEventListener('change', reloadCalendarData);
    }
    if (deviceSelect) {
        deviceSelect.addEventListener('change', reloadCalendarData);
    }

    // فراخوانی اولیه (اگر صفحه رفرش شده و مقادیر مانده‌اند)
    if (serviceSelect && serviceSelect.value) {
        reloadCalendarData();
    }
});