/* static/js/booking-init.js */
/**
 * نقطه شروع سیستم رزرو.
 * اتصال رویدادها و مدیریت جریان داده‌ها.
 */

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Booking System Initializing...');

    // 1. دریافت تنظیمات از فرم HTML
    const configEl = document.getElementById('bookingForm');
    if (!configEl) {
        console.error('Form #bookingForm not found.');
        return;
    }

    // تبدیل نام‌های دیتا-اتریبیوت (hyphen-case) به camelCase
    const config = {
        getServicesUrl: configEl.dataset.getServicesUrl, // data-get-services-url
        getSlotsUrl: configEl.dataset.getSlotsUrl,       // data-get-slots-url
        csrfToken: configEl.dataset.csrfToken,
        priceToPointsRate: parseInt(configEl.dataset.pointsRate) || 0
    };

    // 2. راه‌اندازی اولیه
    BookingState.init();
    
    // راه‌اندازی تقویم (بدون وابستگی به FullCalendar)
    const calendarWrapper = document.getElementById('booking-calendar-wrapper');
    if (window.BookingCalendar && calendarWrapper) {
        BookingCalendar.init(calendarWrapper, (dateObj, dateKey) => {
            // وقتی روی روز کلیک شد
            const slots = BookingCalendar.availableDatesMap[dateKey];
            if (slots && slots.length > 0) {
                BookingState.state.selectedDate = dateKey;
                BookingUI.renderSlots(slots, (selectedSlot) => {
                    // وقتی روی ساعت کلیک شد
                    BookingState.setSlot(selectedSlot.start);
                    
                    // پر کردن فیلد مخفی
                    document.getElementById('selectedSlot').value = selectedSlot.start;
                    
                    // فعال کردن دکمه تایید
                    const confirmBtn = document.getElementById('confirmBtn');
                    if (confirmBtn) {
                        confirmBtn.disabled = false;
                        // اگر مودال تایید دارید، اینجا اتریبیوت دیتا-bs-toggle اضافه کنید یا مستقیم سابمیت
                        confirmBtn.setAttribute('data-bs-toggle', 'modal');
                        confirmBtn.setAttribute('data-bs-target', '#confirmationModal');
                    }
                });
            } else {
                BookingUI.clearSlots();
            }
        });
    }

    // 3. رویداد تغییر "گروه خدمات"
    const serviceGroupSelect = document.getElementById('serviceGroup');
    if (serviceGroupSelect) {
        serviceGroupSelect.addEventListener('change', async function() {
            const groupId = this.value;
            
            // پاک کردن وضعیت قبلی
            BookingUI.clearSelectionArea();
            BookingState.reset();
            BookingCalendar.updateEvents({}); // پاک کردن تقویم

            if (!groupId) return;

            // دریافت خدمات از سرور
            const data = await BookingAPI.fetchServicesForGroup(config.getServicesUrl, groupId);
            
            if (data) {
                BookingUI.renderServices(data.services, data.allow_multiple_selection);
                if (data.has_devices) {
                    BookingUI.renderDevices(data.devices);
                }
                
                // اسکرول نرم به بخش خدمات
                document.getElementById('servicesContainer').scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // 4. رویداد تغییر در لیست خدمات (Delegate Event)
    // چون چک‌باکس‌ها بعداً اضافه می‌شوند، ایونت را به کانتینر پدر می‌دهیم
    document.getElementById('servicesContainer').addEventListener('change', (e) => {
        if (e.target.classList.contains('service-input')) {
            handleSelectionChange();
        }
    });

    // 5. رویداد تغییر دستگاه
    document.getElementById('devicesContainer').addEventListener('change', (e) => {
        if (e.target.classList.contains('device-input')) {
            // پر کردن فیلد مخفی دستگاه
            document.getElementById('selectedDevice').value = e.target.value;
            handleSelectionChange();
        }
    });

    // تابع مدیریت تغییرات (انتخاب سرویس/دستگاه) -> لود مجدد تقویم
    async function handleSelectionChange() {
        // جمع‌آوری سرویس‌های انتخاب شده
        const checkedInputs = document.querySelectorAll('.service-input:checked');
        const serviceIds = Array.from(checkedInputs).map(input => input.value);
        
        // جمع‌آوری قیمت (محاسبه سمت کلاینت برای نمایش سریع)
        let totalPrice = 0;
        checkedInputs.forEach(input => {
            totalPrice += parseInt(input.dataset.price || 0);
        });
        BookingUI.updateFinalPrice(totalPrice);
        document.getElementById('basePrice').value = totalPrice; // ذخیره برای استفاده‌های بعدی

        // بررسی دستگاه
        const deviceSelect = document.getElementById('id_device');
        const deviceId = deviceSelect ? deviceSelect.value : null;

        // اگر دستگاه لازم است ولی انتخاب نشده، تقویم را نگیر
        if (document.getElementById('devicesContainer').innerHTML !== '' && !deviceId) {
            BookingCalendar.updateEvents({});
            return;
        }

        if (serviceIds.length > 0) {
            BookingUI.toggleSlotsLoading(true);
            
            // دریافت تقویم پر
            const slotsData = await BookingAPI.fetchAvailableSlots(
                config.getSlotsUrl, 
                serviceIds, 
                deviceId
            );
            
            BookingUI.toggleSlotsLoading(false);
            
            if (slotsData) {
                BookingCalendar.updateEvents(slotsData);
                // نمایش کانتینر تقویم
                const slotsContainer = document.getElementById('slotsContainer');
                if(slotsContainer) slotsContainer.style.display = 'block';
                
                // اسکرول به تقویم
                document.getElementById('booking-calendar-wrapper').scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            // اگر همه تیک‌ها برداشته شد
            BookingCalendar.updateEvents({});
            BookingUI.clearSlots();
        }
    }
    
    // 6. هندل کردن دکمه تایید نهایی (سابمیت فرم)
    const submitBtn = document.getElementById('submitBtn'); // دکمه داخل مودال
    if (submitBtn) {
        submitBtn.addEventListener('click', () => {
            document.getElementById('bookingForm').submit();
        });
    }
});