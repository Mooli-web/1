// static/js/booking-calendar.js
// --- نسخه v6.3 (Refactor Fix) ---
// این فایل "کتابخانه" رندر کننده تقویم شمسی سفارشی است.
// این فایل به کتابخانه jalali-moment و Namespace سراسری BookingApp نیاز دارد.

/**
 * (حل باگ تاریخ شمسی + کلید ماشینی)
 * موتور رندر تقویم شمسی (Heatmap).
 * @param {object} jMoment - آبجکت jalaliMoment برای ماه جاری
 * @param {object} allGroupedSlots - دیتای اسلات‌ها از API
 * @param {object} todayJalali - آبجکت jalaliMoment برای "امروز"
 */
function buildCalendar(jMoment, allGroupedSlots, todayJalali) {
    
    // --- خواندن متغیرها از Namespace (اصلاح شده در ماموریت قبل) ---
    const calendarGridBody = BookingApp.ui.calendarGridBody;
    calendarGridBody.html('');
    BookingApp.ui.timeSelectionContainer.html('').hide();
    BookingApp.ui.fomoTimerMessage.hide();

    jMoment.locale('fa');
    
    // --- *** اصلاحیه کلیدی: استفاده از 'jMMMM jYYYY' *** ---
    // این خط باید از سال شمسی (jYYYY) استفاده کند نه سال میلادی (YYYY)
    const monthName = jMoment.format('jMMMM jYYYY');
    BookingApp.ui.calendarMonthLabel.text(monthName); 
    // --- *** پایان اصلاحیه *** ---

    const firstDayOfMonth = jMoment.clone().startOf('jMonth');
    const firstDayWeekday = (firstDayOfMonth.day() + 1) % 7;
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

        const dateKey = currentDayMoment.format('jYYYY-jMM-jDD');
        
        if (allGroupedSlots[dateKey]) {
            const slotsForThisDay = allGroupedSlots[dateKey];
            const count = slotsForThisDay.length;

            dayCell.addClass('available');
            
            // --- (مورد ۳) منطق نقشه حرارتی (Heatmap) ---
            // این کد اکنون باید به درستی اجرا شود
            if (count <= 3) {
                dayCell.addClass('available-low'); // قرمز
            } else if (count <= 7) {
                dayCell.addClass('available-medium'); // زرد
            } else {
                dayCell.addClass('available-high'); // سبز
            }
            
            dayCell.data('slots', slotsForThisDay);
            dayCell.data('date-object', currentDayMoment.toDate());
        }
        
        calendarGridBody.append(dayCell);
    }

    // ۳. مدیریت دکمه‌های ماه قبل/بعد
    BookingApp.ui.prevMonthBtn.prop('disabled', jMoment.isSame(todayJalali, 'jMonth'));
}