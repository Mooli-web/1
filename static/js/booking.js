// static/js/booking.js
// --- بازنویسی کامل برای حذف FullCalendar و نمایش لیست اسلات‌ها ---

$(window).on('load', function() {
    console.log("booking.js v3.0 (List View) لود شد.");

    // --- خواندن data attributes از فرم ---
    const bookingForm = $('#bookingForm');
    const GET_SLOTS_URL = bookingForm.attr('data-get-slots-url'); // API اسلات‌ها
    const GET_SERVICES_URL = bookingForm.attr('data-get-services-url');
    const APPLY_DISCOUNT_URL = bookingForm.attr('data-apply-discount-url');
    const CSRF_TOKEN = bookingForm.attr('data-csrf-token');
    const MAX_DISCOUNT = parseFloat(bookingForm.attr('data-max-discount') || 0);

    // --- سلکتورهای اصلی ---
    const serviceGroupSelect = $('#serviceGroup');
    const servicesContainer = $('#servicesContainer');
    const devicesContainer = $('#devicesContainer');
    const selectedDeviceInput = $('#selectedDevice');
    
    // --- سلکتورهای اسلات ---
    const slotsContainer = $('#slotsContainer');
    const selectedSlotInput = $('#selectedSlot');
    const confirmBtn = $('#confirmBtn');
    
    // ... (سایر سلکتورها بدون تغییر) ...
    const submitBtn = $('#submitBtn');
    const applyPointsCheckbox = $('#apply_points');
    const finalPriceSpan = $('#finalPrice');
    const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    const infoConfirmationCheck = $('#infoConfirmationCheck');
    const discountCodeInput = $('#discountCode');
    const applyDiscountBtn = $('#applyDiscountBtn');
    const discountMessage = $('#discountMessage');
    let codeDiscountAmount = 0; 
    const basePriceInput = $('#basePrice');
    const totalDurationInput = $('#totalDuration');

    // ====================================================================
    // --- ۱. توابع کمکی اصلی (محاسبه قیمت و ...) ---
    // ====================================================================

    /**
     * (بدون تغییر) تابع به‌روزرسانی قیمت نهایی
     */
    function updateFinalPrice() {
        let basePrice = parseFloat(basePriceInput.val() || 0);
        let pointsDiscount = 0;

        if (applyPointsCheckbox && applyPointsCheckbox.is(':checked')) {
            let maxPointsDiscount = MAX_DISCOUNT;
            pointsDiscount = Math.min(basePrice, maxPointsDiscount);
        }

        let priceAfterDiscounts = basePrice - pointsDiscount - codeDiscountAmount;
        let finalPrice = Math.max(0, priceAfterDiscounts);
        finalPriceSpan.text(finalPrice.toLocaleString('fa-IR') + ' تومان');

        if (applyPointsCheckbox.length) {
            let maxPointsDiscount = MAX_DISCOUNT;
            let applicableDiscount = Math.min(basePrice, maxPointsDiscount);
            applyPointsCheckbox.next('label').find('strong').last().text(applicableDiscount.toLocaleString('fa-IR') + ' تومان');
        }
    }
    
    /**
     * (جدید) تابع اصلی برای دریافت و نمایش اسلات‌ها
     */
    async function fetchAndDisplaySlots() {
        // ۱. پاک کردن اسلات‌های قبلی
        slotsContainer.html('<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p>در حال جستجوی زمان‌های خالی...</p></div>');
        confirmBtn.prop('disabled', true);
        selectedSlotInput.val('');

        // ۲. جمع‌آوری پارامترها
        let service_ids = [];
        $('.service-item:checked').each(function() {
            service_ids.push($(this).val());
        });
        const deviceId = selectedDeviceInput.val() || '';
        const hasRequiredDevice = $('#deviceSelect').length > 0;

        // ۳. اعتبارسنجی
        if (service_ids.length === 0 || (hasRequiredDevice && !deviceId)) {
            let msg = service_ids.length === 0 
                ? 'لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.' 
                : 'لطفاً دستگاه مورد نظر را انتخاب کنید.';
            slotsContainer.html(`<div class="alert alert-info">${msg}</div>`);
            return;
        }

        // ۴. ساخت URL برای API
        const params = new URLSearchParams();
        service_ids.forEach(id => params.append('service_ids[]', id));
        if (deviceId) {
            params.append('device_id', deviceId);
        }
        const apiUrl = `${GET_SLOTS_URL}?${params.toString()}`;

        try {
            // ۵. فراخوانی API
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('خطا در دریافت اطلاعات از سرور');
            
            const slots = await response.json();

            if (slots.length === 0) {
                slotsContainer.html('<div class="alert alert-warning">متاسفانه هیچ زمان خالی در ۳۰ روز آینده یافت نشد.</div>');
                return;
            }

            // ۶. (بخش اصلی) گروه‌بندی اسلات‌ها بر اساس روز
            const groupedSlots = slots.reduce((acc, slot) => {
                const slotDate = new Date(slot.start);
                
                // ایجاد یک کلید خوانا برای تاریخ (مثل: شنبه، ۲۴ آبان)
                const dateKey = slotDate.toLocaleDateString('fa-IR', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long'
                });

                if (!acc[dateKey]) {
                    acc[dateKey] = [];
                }
                acc[dateKey].push(slot);
                return acc;
            }, {});

            // ۷. رندر کردن HTML
            slotsContainer.html(''); // پاک کردن spinner
            
            for (const dateKey in groupedSlots) {
                // افزودن هدر روز (مثلاً: <h5>شنبه، ۲۴ آبان</h5>)
                slotsContainer.append(`<h5 class="text-muted border-bottom pb-2 mt-4">${dateKey}</h5>`);
                
                const buttonGroup = $('<div class="d-flex flex-wrap gap-2 mb-3"></div>');
                
                groupedSlots[dateKey].forEach(slot => {
                    const slotDate = new Date(slot.start);
                    
                    // فرمت زمان (مثلاً: ۰۹:۳۰)
                    const timeStr = slotDate.toLocaleTimeString('fa-IR', { 
                        hour: '2-digit', 
                        minute: '2-digit', 
                        hour12: false,
                        timeZone: 'Asia/Tehran' // نمایش زمان بر اساس تهران
                    });

                    // --- ایجاد فرمت YYYY-MM-DD HH:MM برای بک‌اند ---
                    // (کپی شده از کد قدیمی booking.js)
                    const d = new Date(slot.start); // استفاده از تاریخ ISO
                    const year = d.getUTCFullYear();
                    const month = (d.getUTCMonth() + 1).toString().padStart(2, '0');
                    const day = d.getUTCDate().toString().padStart(2, '0');
                    const hour = d.getUTCHours().toString().padStart(2, '0');
                    const minute = d.getUTCMinutes().toString().padStart(2, '0');
                    const backendFormat = `${year}-${month}-${day} ${hour}:${minute}`;
                    // --- پایان بخش فرمت بک‌اند ---

                    const button = $(`
                        <button type="button" 
                                class="btn btn-outline-primary" 
                                data-slot-backend-format="${backendFormat}">
                            ${timeStr}
                        </button>
                    `);

                    // افزودن رویداد کلیک برای دکمه
                    button.on('click', function() {
                        slotsContainer.find('button').removeClass('active'); 
                        $(this).addClass('active');
                        
                        selectedSlotInput.val($(this).data('slot-backend-format')); 
                        confirmBtn.prop('disabled', false);
                    });

                    buttonGroup.append(button);
                });
                
                slotsContainer.append(buttonGroup);
            }

        } catch (error) {
            console.error('Error fetching slots:', error);
            slotsContainer.html(`<div class="alert alert-danger">خطا در بارگذاری زمان‌ها: ${error.message}</div>`);
        }
    }


    // ====================================================================
    // --- ۲. رویدادهای مربوط به فرم (انتخاب خدمت، دستگاه و ...) ---
    // ====================================================================

    // --- رویداد انتخاب گروه خدمت ---
    serviceGroupSelect.on('change', async function() {
        console.log("گروه خدمت عوض شد.");
        // ریست کردن همه‌چیز
        servicesContainer.html('');
        devicesContainer.html('');
        selectedDeviceInput.val(''); 
        slotsContainer.html('<div class="alert alert-info">لطفاً ابتدا خدمت و دستگاه (در صورت نیاز) را انتخاب کنید.</div>');
        
        selectedSlotInput.val('');
        confirmBtn.prop('disabled', true);
        basePriceInput.val(0);
        totalDurationInput.val(0);
        codeDiscountAmount = 0;
        discountCodeInput.val('');
        discountMessage.text('').removeClass('text-success text-danger');
        updateFinalPrice();
        
        const groupId = $(this).val();
        if (!groupId) return;

        servicesContainer.html('<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>');

        try {
            const apiUrl = `${GET_SERVICES_URL}?group_id=${groupId}`;
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('خطا در بارگذاری خدمات');
            
            const data = await response.json();
            
            const hasDevices = data.has_devices;
            const devices = data.devices;
            
            if (data.services && data.services.length > 0) {
                let html = '<label class="form-label fs-5">۲. انتخاب خدمات:</label><div class="list-group">';
                const inputType = data.allow_multiple_selection ? 'checkbox' : 'radio';
                data.services.forEach(service => {
                    html += `
                        <label class="list-group-item">
                            <input class="form-check-input me-2 service-item"
                                   type="${inputType}"
                                   name="services[]"
                                   value="${service.id}"
                                   data-price="${service.price}"
                                   data-duration="${service.duration}">
                            ${service.name} - ${parseInt(service.price).toLocaleString('fa-IR')} تومان
                        </label>
                    `;
                });
                html += '</div>';
                servicesContainer.html(html);
            } else {
                servicesContainer.html('<div class="alert alert-warning">خدمتی (زیرگروهی) برای این گروه یافت نشد.</div>');
            }
            
            if (hasDevices && devices && devices.length > 0) {
                let html = `
                    <label for="deviceSelect" class="form-label fs-5">۳. انتخاب دستگاه:</label>
                    <select id="deviceSelect" class="form-select form-select-lg" required>
                        <option value="">--- انتخاب کنید ---</option>
                `;
                devices.forEach(d => {
                    html += `<option value="${d.id}">${d.name}</option>`;
                });
                html += '</select>';
                devicesContainer.html(html);
                
                // تغییر لیبل اسلات‌ها
                slotsContainer.before('<label class="form-label fs-5 mt-3">۴. انتخاب زمان:</label>');

            } else if (hasDevices) {
                devicesContainer.html('<div class="alert alert-danger">این گروه خدماتی نیاز به دستگاه دارد، اما هیچ دستگاهی برای آن تنظیم نشده است.</div>');
            } else {
                 // اگر دستگاه نیاز نداشت، لیبل اسلات‌ها را عوض کن
                 slotsContainer.before('<label class="form-label fs-5 mt-3">۳. انتخاب زمان:</label>');
            }
        } catch (error) {
            servicesContainer.html(`<div class="alert alert-danger">${error.message}</div>`);
        }
    });

    /**
     * رویداد انتخاب خدمت (چک‌باکس یا رادیوباتن)
     */
    $(document).on('change', '.service-item', function() {
        console.log("خدمت عوض شد.");
        let currentBasePrice = 0;
        let currentTotalDuration = 0;

        $('.service-item:checked').each(function() {
            currentBasePrice += parseFloat($(this).data('price'));
            currentTotalDuration += parseFloat($(this).data('duration'));
        });

        basePriceInput.val(currentBasePrice);
        totalDurationInput.val(currentTotalDuration);

        codeDiscountAmount = 0;
        discountCodeInput.val('');
        discountMessage.text('').removeClass('text-success text-danger');
        updateFinalPrice();
        
        // --- مهم: فراخوانی تابع جدید ---
        fetchAndDisplaySlots();
    });
    
    /**
     * رویداد انتخاب دستگاه
     */
    $(document).on('change', '#deviceSelect', function() {
        selectedDeviceInput.val($(this).val());
        console.log("دستگاه عوض شد.");

        // --- مهم: فراخوانی تابع جدید ---
        fetchAndDisplaySlots();
    });

    // ====================================================================
    // --- ۳. رویدادهای تخفیف و ثبت نهایی (کاملاً بدون تغییر) ---
    // ====================================================================

    // اعمال/حذف تخفیف امتیاز
    if (applyPointsCheckbox) {
        applyPointsCheckbox.on('change', updateFinalPrice);
    }

    // دکمه "اعمال کد" تخفیف
    applyDiscountBtn.on('click', async function() {
        const code = discountCodeInput.val();
        const currentBasePrice = parseFloat(basePriceInput.val() || 0);

        if (!code || currentBasePrice === 0) {
            discountMessage.text('لطفاً ابتدا خدمت و کد را وارد کنید.').removeClass('text-success').addClass('text-danger');
            return;
        }
        
        const formData = new FormData();
        formData.append('code', code);
        formData.append('total_price', currentBasePrice);
        formData.append('csrfmiddlewaretoken', CSRF_TOKEN);

        try {
            const response = await fetch(APPLY_DISCOUNT_URL, {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                if (response.status === 400 || response.status === 404) {
                    const data = await response.json();
                    throw new Error(data.message || 'خطای ناشناخته');
                } else {
                    throw new Error(`خطای سرور: ${response.status}`);
                }
            }
            
            const data = await response.json();
            
            if (data.discount_amount !== undefined) {
                codeDiscountAmount = parseFloat(data.discount_amount);
                discountMessage.text(`تخفیف ${parseInt(data.discount_amount).toLocaleString('fa-IR')} تومانی اعمال شد.`).removeClass('text-danger').addClass('text-success');
            }
            
        } catch (error) {
            console.error("Error applying discount:", error);
            codeDiscountAmount = 0; 
            discountMessage.text(error.message).removeClass('text-success').addClass('text-danger');
        }
        updateFinalPrice();
    });

    // --- رویدادهای دکمه تایید و مودال ---
    confirmBtn.on('click', function() {
        const deviceSelect = $('#deviceSelect');
        if (deviceSelect.length > 0 && !selectedDeviceInput.val()) {
             alert('لطفا دستگاه مورد نظر را انتخاب کنید.');
             deviceSelect.focus();
             return;
        }
        
        if (bookingForm[0].checkValidity() && $('.service-item:checked').length > 0 && selectedSlotInput.val()) {
            if ($('#manual_confirm').is(':checked')) {
                bookingForm.submit();
            } else {
                confirmationModal.show();
            }
        } else {
            bookingForm[0].reportValidity();
            if ($('.service-item:checked').length === 0) {
                alert('لطفا حداقل یک خدمت را انتخاب کنید.');
            }
            if (!selectedSlotInput.val()) {
                alert('لطفا زمان نوبت را انتخاب کنید.');
            }
        }
    });

    infoConfirmationCheck.on('change', function() {
        submitBtn.prop('disabled', !this.checked);
    });

    submitBtn.on('click', function() {
        bookingForm.submit();
    });
    
    // --- اجرای اولیه ---
    updateFinalPrice();
});