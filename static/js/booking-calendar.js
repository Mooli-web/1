// static/js/booking-calendar.js
// --- نسخه v6.2 (کلید ماشینی) ---
// این فایل "کتابخانه" رندر کننده تقویم شمسی سفارشی است.
// این فایل به کتابخانه jalali-moment نیاز دارد.

/**
 * (حل باگ تاریخ شمسی + کلید ماشینی)
 * موتور رندر تقویم شمسی (Heatmap).
 * @param {object} jMoment - آبجکت jalaliMoment برای ماه جاری
 * @param {object} allGroupedSlots - دیتای اسلات‌ها از API
 * @param {object} todayJalali - آبجکت jalaliMoment برای "امروز"
 */
function buildCalendar(jMoment, allGroupedSlots, todayJalali) {
    const calendarGridBody = $('#calendar-grid-body');
    calendarGridBody.html(''); // پاک کردن گرید قبلی
    timeSelectionContainer.html('').hide(); // مخفی کردن ساعت‌ها
    fomoTimerMessage.hide(); // مخفی کردن تایمر

    // تنظیم زبان "فارسی" برای اطمینان
    jMoment.locale('fa');
    
    // نام ماه شمسی (e.g., "آبان ۱۴۰۴")
    const monthName = jMoment.format('jMMMM jYYYY');
    $('#calendar-month-label').text(monthName);

    // یافتن روز هفته برای روز اول ماه (0=شنبه، 6=جمعه)
    const firstDayOfMonth = jMoment.clone().startOf('jMonth');
    const firstDayWeekday = firstDayOfMonth.day(); // 0-6
    const daysInMonth = jMoment.jDaysInMonth();

    // ۱. اضافه کردن خانه‌های خالی (padding) قبل از شروع ماه
    for (let i = 0; i < firstDayWeekday; i++) {
        calendarGridBody.append('<div class="calendar-day-empty"></div>');
    }

    // ۲. رندر کردن روزهای ماه
    for (let day = 1; day <= daysInMonth; day++) {
        const dayCell = $(`<div class="calendar-day">${day}</div>`);
        const currentDayMoment = jMoment.clone().jDate(day);

        // ۳. بررسی روزهای گذشته (امروز قابل رزرو است)
        if (currentDayMoment.isBefore(todayJalali, 'day')) {
            dayCell.addClass('past-day');
            calendarGridBody.append(dayCell);
            continue;
        }

        // ۴. (اصلاحیه حیاتی) استفاده از کلید ماشینی (jYYYY-jMM-jDD)
        // این کلید به زبان (locale) یا ویرگول وابسته نیست.
        const dateKey = currentDayMoment.format('jYYYY-jMM-jDD');
        
        if (allGroupedSlots[dateKey]) {
            const slotsForThisDay = allGroupedSlots[dateKey];
            const count = slotsForThisDay.length;

            dayCell.addClass('available');
            
            // منطق رنگ‌بندی (نقشه حرارتی)
            if (count <= 3) {
                dayCell.addClass('available-low'); // قرمز
            } else if (count <= 7) {
                dayCell.addClass('available-medium'); // زرد
            } else {
                dayCell.addClass('available-high'); // سبز
            }
            
            // ضمیمه کردن دیتای اسلات‌ها به خود دکمه روز
            dayCell.data('slots', slotsForThisDay);
            // ضمیمه کردن فرمت تاریخ (برای ایده ۳)
            dayCell.data('date-object', currentDayMoment.toDate());
        }
        
        calendarGridBody.append(dayCell);
    }

    // ۳. مدیریت دکمه‌های ماه قبل/بعد
    $('#calendar-prev-month').prop('disabled', jMoment.isSame(todayJalali, 'jMonth'));
}