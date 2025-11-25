/* static/js/booking-calendar.js */
/**
 * مدیریت تقویم شمسی.
 * استفاده از moment-jalaali برای محاسبات تاریخ.
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

        // مطمئن شویم moment وجود دارد
        if (typeof moment === 'undefined') {
            console.error('Jalali Moment library missing!');
            return;
        }

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
        
        if (this.elements.monthLabel) {
            this.elements.monthLabel.textContent = startOfMonth.format('jMMMM jYYYY');
        }

        this.elements.gridBody.innerHTML = '';

        // شنبه=0 در تقویم شمسی
        const startDayOfWeek = startOfMonth.weekday(); 

        // خانه‌های خالی
        for (let i = 0; i < startDayOfWeek; i++) {
            const empty = document.createElement('div');
            empty.className = 'calendar-day calendar-day-empty';
            this.elements.gridBody.appendChild(empty);
        }

        const daysInMonth = moment.jDaysInMonth(startOfMonth.jYear(), startOfMonth.jMonth());
        const todayStr = moment().format('YYYY-MM-DD');

        for (let i = 1; i <= daysInMonth; i++) {
            const dayDate = startOfMonth.clone().jDate(i);
            const dateKey = dayDate.format('YYYY-MM-DD');
            
            const cell = document.createElement('div');
            cell.className = 'calendar-day';
            cell.textContent = i;

            const hasSlots = this.availableDatesMap[dateKey] && this.availableDatesMap[dateKey].length > 0;
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
                    if (this.onDateSelect) this.onDateSelect(dayDate.toDate(), dateKey);
                });
            } else {
                cell.classList.add('unavailable');
            }

            this.elements.gridBody.appendChild(cell);
        }
        
        // مدیریت دکمه "ماه قبل"
        if (this.elements.prevBtn) {
            const prevMonthEnd = startOfMonth.clone().subtract(1, 'jMonth').endOf('jMonth');
            this.elements.prevBtn.disabled = prevMonthEnd.isBefore(moment(), 'day');
        }
    }
};

window.BookingCalendar = BookingCalendar;