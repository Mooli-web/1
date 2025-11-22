/* static/js/booking-ui.js */
/**
 * مدیریت رابط کاربری (UI).
 * وظیفه به‌روزرسانی DOM، نمایش لودینگ و تغییر وضعیت دکمه‌ها را دارد.
 */

const BookingUI = {
    elements: {
        calendarContainer: document.getElementById('calendar-container'),
        slotsContainer: document.getElementById('slots-container'),
        loadingSpinner: document.getElementById('loading-spinner'),
        servicesSelect: document.getElementById('id_services'), // فرض بر این است که ID اینپوت جنگو این است
        confirmButton: document.getElementById('btn-confirm-booking'),
        totalPriceDisplay: document.getElementById('total-price-display'),
    },

    /**
     * نمایش یا مخفی کردن لودینگ
     * @param {boolean} show 
     */
    toggleLoading(show) {
        if (this.elements.loadingSpinner) {
            this.elements.loadingSpinner.style.display = show ? 'block' : 'none';
        }
        if (this.elements.slotsContainer) {
            this.elements.slotsContainer.style.opacity = show ? '0.5' : '1';
        }
    },

    /**
     * رندر کردن اسلات‌های زمانی در صفحه
     * @param {Array} slots - لیست اسلات‌ها برای یک روز خاص
     * @param {Function} onSlotSelect - تابع کال‌بک هنگام کلیک روی اسلات
     */
    renderSlots(slots, onSlotSelect) {
        const container = this.elements.slotsContainer;
        if (!container) return;

        container.innerHTML = ''; // پاک کردن قبلی‌ها

        if (!slots || slots.length === 0) {
            container.innerHTML = '<div class="alert alert-warning">هیچ نوبت خالی برای این تاریخ یافت نشد.</div>';
            return;
        }

        const list = document.createElement('div');
        list.className = 'd-flex flex-wrap gap-2';

        slots.forEach(slot => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-primary slot-btn';
            // نمایش ساعت به کاربر (فرض: slot.readable_start شامل متن فارسی است)
            // اما معمولا فقط ساعت را روی دکمه می‌نویسیم
            const timePart = slot.start.split('T')[1].substring(0, 5); // استخراج 14:30 از ISO
            btn.textContent = timePart; 
            
            btn.dataset.start = slot.start;
            
            btn.addEventListener('click', (e) => {
                // حذف کلاس active از همه دکمه‌ها
                document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('active'));
                // افزودن به دکمه فعلی
                btn.classList.add('active');
                
                // فراخوانی کال‌بک
                if (typeof onSlotSelect === 'function') {
                    onSlotSelect(slot);
                }
            });

            list.appendChild(btn);
        });

        container.appendChild(list);
    },

    /**
     * پاک کردن لیست اسلات‌ها
     */
    clearSlots() {
        if (this.elements.slotsContainer) {
            this.elements.slotsContainer.innerHTML = '<p class="text-muted">لطفاً یک تاریخ را از تقویم انتخاب کنید.</p>';
        }
    },

    /**
     * به‌روزرسانی قیمت نهایی
     * @param {number} price 
     */
    updatePrice(price) {
        if (this.elements.totalPriceDisplay) {
            // فرمت کردن عدد به صورت سه رقم سه رقم
            this.elements.totalPriceDisplay.textContent = price.toLocaleString('fa-IR');
        }
    }
};

window.BookingUI = BookingUI;