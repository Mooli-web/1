// static/js/booking-calendar.js
// --- نسخه v6.4 (Fix: Calendar Rendering Logic) ---
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
    const monthName = jMoment.format('jMMMM jYYYY');
    
    // ==========================================================
    // --- اصلاحیه نهایی: فارسی سازی اعداد سال ---
    // یک تابع کمکی کوچک برای تبدیل اعداد انگلیسی به فارسی
    const toFarsiDigits = (s) => s.toString().replace(/\d/g, x => ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'][x]);
    
    // ما خروجی را (مثلاً "آبان 1404") گرفته و اعداد آن را فارسی می‌کنیم
    BookingApp.ui.calendarMonthLabel.text(toFarsiDigits(monthName));
    // ==========================================================


    const firstDayOfMonth = jMoment.clone().startOf('jMonth');
    const firstDayWeekday = (firstDayOfMonth.day() + 1) % 7;
    const daysInMonth = jMoment.jDaysInMonth();

    // ۱. اضافه کردن خانه‌های خالی (padding) قبل از شروع ماه
    for (let i = 0; i < firstDayWeekday; i++) {
        calendarGridBody.append('<div class="calendar-day-empty"></div>');
    }

    // ==========================================================
    // --- *** شروع اصلاحیه: بازنویسی منطق رندر روزها *** ---
    // ==========================================================
    for (let day = 1; day <= daysInMonth; day++) {
        
        // ۱. سلول و آبجکت moment آن روز را بساز
        const dayCell = $(`<div class="calendar-day">${day}</div>`);
        const currentDayMoment = jMoment.clone().jDate(day);

        // ۲. بررسی کن آیا روز در گذشته است یا امروز/آینده
        if (currentDayMoment.isBefore(todayJalali, 'day')) {
            // اگر در گذشته بود، کلاس 'past-day' (که استایل پیش‌فرض .calendar-day است)
            // اعمال می‌شود و هیچ کار دیگری لازم نیست.
            // dayCell.addClass('past-day'); // این خط اضافی است چون CSS پیش‌فرض همین است
        } else {
            // اگر امروز یا در آینده بود، بررسی کن اسلات خالی دارد یا نه
            const dateKey = currentDayMoment.format('jYYYY-jMM-jDD');
            
            if (allGroupedSlots[dateKey]) {
                // اگر اسلات داشت، آن را "available" کن
                const slotsForThisDay = allGroupedSlots[dateKey];
                const count = slotsForThisDay.length;

                dayCell.addClass('available'); // این کلاس استایل خاکستری پیش‌فرض را لغو می‌کند
                
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
            // اگر اسلات نداشت (else)، هیچ کلاسی اضافه نمی‌شود
            // و سلول با استایل پیش‌فرض (خاکستری) رندر می‌شود
        }
        
        // ۳. در هر صورت (چه گذشته، چه آینده، چه با اسلات، چه بی اسلات)
        // سلول را به تقویم اضافه کن.
        calendarGridBody.append(dayCell);
    }
    // ==========================================================
    // --- *** پایان اصلاحیه *** ---
    // ==========================================================

    // ۳. مدیریت دکمه‌های ماه قبل/بعد
    BookingApp.ui.prevMonthBtn.prop('disabled', jMoment.isSame(todayJalali, 'jMonth'));
}