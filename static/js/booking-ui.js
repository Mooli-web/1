/* static/js/booking-ui.js */
/**
 * مدیریت رابط کاربری (UI).
 * وظیفه ساختن چک‌باکس‌ها، دکمه‌ها و نمایش تقویم.
 */

const BookingUI = {
    elements: {
        servicesContainer: document.getElementById('servicesContainer'),
        devicesContainer: document.getElementById('devicesContainer'),
        slotsContainer: document.getElementById('slotsContainer'),
        slotsLoader: document.getElementById('slots-loader'),
        totalPriceDisplay: document.getElementById('finalPrice'),
        slotsInitialMessage: document.getElementById('slots-initial-message'),
        // المان‌های دیگر در صورت نیاز...
    },

    /**
     * نمایش لیست خدمات (چک‌باکس یا رادیو)
     */
    renderServices(services, allowMultiple) {
        const container = document.getElementById('servicesContainer');
        if (!container) return;

        container.innerHTML = '<label class="form-label fs-5">۲. انتخاب خدمات:</label>';
        
        if (!services || services.length === 0) {
            container.innerHTML += '<div class="alert alert-warning">خدمتی در این گروه یافت نشد.</div>';
            return;
        }

        const listDiv = document.createElement('div');
        listDiv.className = 'list-group';

        services.forEach(service => {
            const type = allowMultiple ? 'checkbox' : 'radio';
            // فرمت قیمت سه رقم سه رقم
            const priceFormatted = service.price.toLocaleString('fa-IR');
            
            const itemHtml = `
                <label class="list-group-item d-flex justify-content-between align-items-center cursor-pointer">
                    <div>
                        <input class="form-check-input me-2 service-input" type="${type}" 
                               name="services[]" value="${service.id}" 
                               data-price="${service.price}" data-duration="${service.duration}">
                        <span class="fw-bold">${service.name}</span>
                        <small class="text-muted d-block me-4">${service.duration} دقیقه</small>
                    </div>
                    <span class="badge bg-light text-dark border">${priceFormatted} تومان</span>
                </label>
            `;
            listDiv.innerHTML += itemHtml;
        });

        container.appendChild(listDiv);
    },

    /**
     * نمایش لیست دستگاه‌ها (در صورت نیاز)
     */
    renderDevices(devices) {
        const container = document.getElementById('devicesContainer');
        if (!container) return;
        
        container.innerHTML = ''; // پاک کردن قبلی
        
        if (!devices || devices.length === 0) return;

        container.innerHTML = '<label class="form-label fs-5">۳. انتخاب دستگاه:</label>';
        
        const select = document.createElement('select');
        select.className = 'form-select form-select-lg device-input';
        select.name = 'device_id';
        select.id = 'id_device'; // شناسه برای دسترسی راحت‌تر
        
        let options = '<option value="">--- انتخاب دستگاه ---</option>';
        devices.forEach(dev => {
            options += `<option value="${dev.id}">${dev.name}</option>`;
        });
        select.innerHTML = options;
        
        container.appendChild(select);
    },

    /**
     * پاک کردن ورودی‌ها هنگام تغییر گروه
     */
    clearSelectionArea() {
        if (this.elements.servicesContainer) this.elements.servicesContainer.innerHTML = '';
        if (this.elements.devicesContainer) this.elements.devicesContainer.innerHTML = '';
        this.clearSlots();
    },

    /**
     * نمایش لودینگ اسلات‌ها
     */
    toggleSlotsLoading(show) {
        const container = document.getElementById('slotsContainer');
        const loader = document.getElementById('slots-loader');
        const initMsg = document.getElementById('slots-initial-message');
        
        if (container) container.style.display = 'block'; // کانتینر اصلی همیشه باشد
        if (loader) loader.style.display = show ? 'block' : 'none';
        
        // وقتی لودینگ هست یا نتیجه آمده، پیام اولیه را مخفی کن
        if (show && initMsg) initMsg.style.display = 'none';
    },

    /**
     * رندر اسلات‌های ساعت
     */
    renderSlots(slots, onSlotSelect) {
        const container = document.getElementById('time-selection-container');
        if (!container) return;

        container.innerHTML = '<h5 class="mb-3">زمان‌های موجود برای این روز:</h5>';
        container.style.display = 'block';

        const list = document.createElement('div');
        list.className = 'd-flex flex-wrap gap-2';

        slots.forEach(slot => {
            // استخراج ساعت از فرمت ISO (مثلاً 2023-11-20T14:30:00)
            // فرض: ماژول moment-jalaali یا تبدیل ساده
            const timePart = slot.start.split('T')[1].slice(0, 5); 

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-primary px-4 py-2 slot-btn';
            btn.innerHTML = `<i class="bi bi-clock me-1"></i> ${timePart}`;
            
            btn.addEventListener('click', () => {
                document.querySelectorAll('.slot-btn').forEach(b => {
                    b.classList.remove('active', 'btn-primary');
                    b.classList.add('btn-outline-primary');
                });
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('active', 'btn-primary');
                
                if (onSlotSelect) onSlotSelect(slot);
            });

            list.appendChild(btn);
        });

        container.appendChild(list);
        
        // اسکرول به بخش ساعت‌ها
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    },

    clearSlots() {
        const container = document.getElementById('time-selection-container');
        if (container) {
            container.innerHTML = '';
            container.style.display = 'none';
        }
        // بازگرداندن پیام اولیه اگر هنوز سرویسی انتخاب نشده (اختیاری)
        // const initMsg = document.getElementById('slots-initial-message');
        // if (initMsg) initMsg.style.display = 'block';
    },

    updateFinalPrice(price) {
        const el = document.getElementById('finalPrice');
        if (el) el.textContent = price.toLocaleString('fa-IR') + ' تومان';
        
        // فعال/غیرفعال کردن دکمه
        const btn = document.getElementById('confirmBtn');
        if (btn) btn.disabled = false; // یا منطق پیچیده‌تر
    }
};

window.BookingUI = BookingUI;