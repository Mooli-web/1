// static/js/booking-calendar.js
// --- نسخه v7.1 (Refactor Complete: Cleaned) ---
// این فایل "کتابخانه" رندر کننده تقویم شمسی سفارشی است.
// این فایل به کتابخانه jalali-moment و Namespace سراسری BookingApp نیاز دارد.

/**
 * (حل باگ تاریخ شمسی + کلید ماشینی)
 * موتور رندر تقویم شمسی (Heatmap).
 * @param {object} jMoment - آبجکت jalaliMoment برای ماه جاری
 * @param {object} allGroupedSlots - دیتای اسلات‌ها از API (آماده شده توسط بک‌اند)
 * @param {object} todayJalali - آبجکت jalaliMoment برای "امروز"
 */
function buildCalendar(jMoment, allGroupedSlots, todayJalali) {
    
    // (کدهای دیباگ حذف شدند)

    // --- خواندن متغیرها از Namespace ---
    const calendarGridBody = BookingApp.ui.calendarGridBody;
    calendarGridBody.html('');
    BookingApp.ui.timeSelectionContainer.html('').hide();
    BookingApp.ui.fomoTimerMessage.hide();

    jMoment.locale('fa');
    
    const monthName = jMoment.format('jMMMM jYYYY');
    
    // ==========================================================
    // --- فارسی سازی اعداد سال ---
    const toFarsiDigits = (s) => s.toString().replace(/\d/g, x => ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'][x]);
    BookingApp.ui.calendarMonthLabel.text(toFarsiDigits(monthName));
    // ==========================================================


    const firstDayOfMonth = jMoment.clone().startOf('jMonth');
    const firstDayWeekday = (firstDayOfMonth.day() + 1) % 7; // (شنبه = 0)
    const daysInMonth = jMoment.jDaysInMonth();

    // ۱. اضافه کردن خانه‌های خالی (padding) قبل از شروع ماه
    for (let i = 0; i < firstDayWeekday; i++) {
        calendarGridBody.append('<div class="calendar-day-empty"></div>');
    }

    // ==========================================================
    // --- منطق رندر روزها ---
    // ==========================================================
    for (let day = 1; day <= daysInMonth; day++) {
        
        // ۱. سلول و آبجکت moment آن روز را بساز
        const dayCell = $(`<div class="calendar-day">${day}</div>`);
        const currentDayMoment = jMoment.clone().jDate(day);

        // ۲. بررسی کن آیا روز در گذشته است یا امروز/آینده
        if (currentDayMoment.isBefore(todayJalali, 'day')) {
            // روز گذشته است (استایل پیش‌فرض خاکستری اعمال می‌شود)
        } else {
            // اگر امروز یا در آینده بود، بررسی کن اسلات خالی دارد یا نه
            
            // این کلید مصرفی (مثلاً '1404-08-26') است
            const dateKey = currentDayMoment.format('jYYYY-jMM-jDD');
            
            // (کد دیباگ حذف شد)

            // allGroupedSlots اکنون آبجکت آماده از بک‌اند است
            if (allGroupedSlots && allGroupedSlots[dateKey]) { 
                // اگر اسلات داشت، آن را "available" کن
                const slotsForThisDay = allGroupedSlots[dateKey];
                const count = slotsForThisDay.length;

                dayCell.addClass('available');
                
                // --- منطق نقشه حرارتی (Heatmap) ---
                if (count <= 3) {
                    dayCell.addClass('available-low'); // قرمز
                } else if (count <= 7) {
                    dayCell.addClass('available-medium'); // زرد
                } else {
                    dayCell.addClass('available-high'); // سبز
                }
                
                // دیتا را برای کلیک کردن به سلول متصل کن
                dayCell.data('slots', slotsForThisDay);
                dayCell.data('date-object', currentDayMoment.toDate());
            }
            // اگر اسلات نداشت (else)، با استایل پیش‌فرض (خاکستری) رندر می‌شود
        }
        
        // ۳. سلول را به تقویم اضافه کن
        calendarGridBody.append(dayCell);
    }
    // ==========================================================

    // ۳. مدیریت دکمه‌های ماه قبل/بعد
    BookingApp.ui.prevMonthBtn.prop('disabled', jMoment.isSame(todayJalali, 'jMonth'));
}