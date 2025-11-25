/* static/js/booking-calendar.js */
/**
 * مدیریت تقویم شمسی.
 * اصلاح نهایی: هماهنگی کامل فرمت تاریخ (شمسی + اعداد انگلیسی)
 */

const BookingCalendar = {
    currentMonth: null, 
    availableDatesMap: {}, 
    elements: {
        wrapper: null,
        gridBody: null,
        monthLabel: null,
        prevBtn: null,
        nextBtn: null,
    },
    onDateSelect: null,

    init(wrapperEl, onDateSelect) {
        if (!wrapperEl) return;

        this.elements.wrapper = wrapperEl;
        this.elements.gridBody = document.getElementById('calendar-grid-body');
        this.elements.monthLabel = document.getElementById('calendar-month-label');
        this.elements.prevBtn = document.getElementById('calendar-prev-month');
        this.elements.nextBtn = document.getElementById('calendar-next-month');
        this.onDateSelect = onDateSelect;

        if (typeof moment === 'undefined') {
            console.error('Jalali Moment library missing!');
            return;
        }

        // زبان پیش‌فرض برای نمایش (هدر ماه و...) فارسی باشد
        this.currentMonth = moment().locale('fa').startOf('jMonth');

        if (this.elements.prevBtn) {
            this.elements.prevBtn.addEventListener('click', () => this.changeMonth(-1));
        }
        if (this.elements.nextBtn) {
            this.elements.nextBtn.addEventListener('click', () => this.changeMonth(1));
        }

        this.render();
    },

    changeMonth(step) {
        this.currentMonth.add(step, 'jMonth');
        this.render();
    },

    updateEvents(slotsData) {
        this.availableDatesMap = slotsData || {};
        this.render();
    },

    render() {
        if (!this.elements.gridBody) return;

        const startOfMonth = this.currentMonth.clone().startOf('jMonth');
        
        // نمایش عنوان ماه (مثلاً: آذر ۱۴۰۴)
        if (this.elements.monthLabel) {
            this.elements.monthLabel.textContent = startOfMonth.format('jMMMM jYYYY');
        }

        this.elements.gridBody.innerHTML = '';

        const startDayOfWeek = startOfMonth.weekday(); 

        // خانه‌های خالی اول ماه
        for (let i = 0; i < startDayOfWeek; i++) {
            const empty = document.createElement('div');
            empty.className = 'calendar-day calendar-day-empty';
            this.elements.gridBody.appendChild(empty);
        }

        const daysInMonth = moment.jDaysInMonth(startOfMonth.jYear(), startOfMonth.jMonth());
        
        // اصلاح مهم ۱: تولید تاریخ امروز به صورت "شمسی" و با "اعداد انگلیسی" برای مقایسه
        const todayStr = moment().locale('en').format('jYYYY-jMM-jDD');

        for (let i = 1; i <= daysInMonth; i++) {
            const dayDate = startOfMonth.clone().jDate(i);
            
            // اصلاح مهم ۲: استفاده از jYYYY برای تاریخ شمسی + locale('en') برای اعداد انگلیسی
            // خروجی این خط دقیقاً مثل سرور می‌شود: "1404-09-04"
            const dateKey = dayDate.clone().locale('en').format('jYYYY-jMM-jDD');
            
            const cell = document.createElement('div');
            cell.className = 'calendar-day';
            cell.textContent = i; // عدد روز برای نمایش به کاربر

            const hasSlots = this.availableDatesMap[dateKey] && this.availableDatesMap[dateKey].length > 0;
            
            // مقایسه رشته‌ای تاریخ‌ها (چون هر دو فرمت یکسان YYYY-MM-DD دارند، مقایسه صحیح است)
            const isPast = dateKey < todayStr;

            if (isPast) {
                cell.classList.add('disabled');
                cell.style.opacity = '0.5';
            } else if (hasSlots) {
                cell.classList.add('available');
                cell.style.backgroundColor = '#d4edda';
                cell.style.color = '#155724';
                
                cell.addEventListener('click', () => {
                    this.elements.gridBody.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected'));
                    cell.classList.add('selected');
                    // ارسال دیتای انتخاب شده
                    if (this.onDateSelect) this.onDateSelect(dayDate.toDate(), dateKey);
                });
            } else {
                cell.classList.add('unavailable');
            }

            this.elements.gridBody.appendChild(cell);
        }
        
        if (this.elements.prevBtn) {
            const prevMonthEnd = startOfMonth.clone().subtract(1, 'jMonth').endOf('jMonth');
            this.elements.prevBtn.disabled = prevMonthEnd.isBefore(moment(), 'day');
        }
    }
};

window.BookingCalendar = BookingCalendar;