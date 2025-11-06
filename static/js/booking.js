// mooli-web/1/1-108afa36b6d3b8572ca403177904f4e3aab9489b/static/js/booking.js
$(document).ready(function() {
    console.log("booking.js لود شد (نسخه flatpickr-jalali-support v3 - Fix نهایی).");

    // --- خواندن data attributes از فرم ---
    const bookingForm = $('#bookingForm');
    
    const GET_SLOTS_URL = bookingForm.attr('data-get-slots-url');
    const GET_MONTH_URL = bookingForm.attr('data-get-month-availability-url');
    const GET_SERVICES_URL = bookingForm.attr('data-get-services-url');
    const APPLY_DISCOUNT_URL = bookingForm.attr('data-apply-discount-url');
    const CSRF_TOKEN = bookingForm.attr('data-csrf-token');
    const MAX_DISCOUNT = parseFloat(bookingForm.attr('data-max-discount') || 0);

    // --- سلکتورهای اصلی ---
    const serviceGroupSelect = $('#serviceGroup');
    const servicesContainer = $('#servicesContainer');
    const devicesContainer = $('#devicesContainer');
    const selectedDeviceInput = $('#selectedDevice');
    
    // --- سلکتورهای تقویم ---
    const datePickerInput = $('#datePickerInput'); 
    const calendarContainer = $('#calendarContainer');
    const gregorianDateInput = $('#gregorianDateInput');
    
    const slotsContainer = $('#slotsContainer');
    const selectedSlotInput = $('#selectedSlot');
    const confirmBtn = $('#confirmBtn');
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
    
    let allowMultipleSelection = false;
    let calendarInstance = null;
    let currentMonthData = {}; 

    /**
     * تابع به‌روزرسانی قیمت نهایی
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
     * [جایگزین شده با flatpickr-jalali-support]
     */
    async function updateCalendarAvailability(year, month) {
        console.log(`۱. updateCalendarAvailability فراخوانی شد برای ماه جلالی: ${year}-${month}`);

        const totalDuration = totalDurationInput.val();
        let service_ids = [];
        $('.service-item:checked').each(function() {
            service_ids.push($(this).val());
        });

        if (!totalDuration || totalDuration == 0 || service_ids.length === 0) {
            if(calendarInstance) calendarInstance.destroy();
            calendarInstance = null;
            calendarContainer.html('<div class="alert alert-info">لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.</div>');
            datePickerInput.val('').attr('placeholder', 'لطفاً ابتدا خدمت را انتخاب کنید...');
            console.warn("هیچ خدمتی انتخاب نشده. تقویم پاک شد.");
            return;
        }

        calendarContainer.html('<div class="text-center p-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>');
        datePickerInput.attr('placeholder', 'در حال بارگذاری تقویم...');
        console.log("۲. در حال بارگذاری... (ارسال درخواست به API)");

        const serviceParams = service_ids.map(id => `service_ids[]=${id}`).join('&');
        const deviceId = selectedDeviceInput.val() || ''; 

        try {
            const url = `${GET_MONTH_URL}?year=${year}&month=${month}&total_duration=${totalDuration}&${serviceParams}&device_id=${deviceId}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("خطای سرور در دریافت ماه:", errorText);
                throw new Error(`خطای سرور: ${response.status}`);
            }
            
            currentMonthData = await response.json(); 
            console.log("۳. دیتا با موفقیت دریافت و پارس شد:", currentMonthData);

            if (calendarInstance) {
                calendarInstance.destroy();
            }
            
            calendarContainer.html(''); 
            console.log("۵. در حال ساخت تقویم جدید flatpickr-jalali-support...");
        
            // =================================================================
            // *** شروع پیاده‌سازی flatpickr-jalali-support ***
            // =================================================================
            
            // تابع کمکی برای تبدیل تاریخ میلادی flatpickr به رشته جلالی
            // این تابع به persian-date.js که در HTML لود شده، متکی است
            function getJalaliDateString(dateObj) {
                const pDate = new persianDate(dateObj);
                return `${pDate.year()}-${pDate.month()}-${pDate.date()}`;
            }

            calendarInstance = flatpickr(calendarContainer, {
                inline: true,
                // --- فعال‌سازی تقویم جلالی (این کتابخانه fa را می‌شناسد) ---
                locale: "fa",
                
                // --- بخش plugins حذف شد، چون پلاگین در خود این کتابخانه ادغام شده ---

                // تنظیم ماه و سال پیش‌فرض جلالی
                defaultDate: new persianDate([year, month, 1]).gregorianDate,
                
                onDayCreate: function(dObj, dStr, fp, dayElem) {
                    // ما به کتابخانه persian-date.js (که جداگانه لود کردیم) تکیه می‌کنیم
                    // تا تاریخ جلالی را از آبجکت تاریخ میلادی استخراج کنیم.
                    const pDate = new persianDate(dayElem.dateObj);
                    const jDateStr = `${pDate.year()}-${pDate.month()}-${pDate.date()}`;
                    
                    const status = currentMonthData[jDateStr]; 
                    
                    if (status) {
                        dayElem.classList.add(`day-${status}`);
                        if (status !== 'available') {
                            dayElem.classList.add("flatpickr-disabled");
                        }
                    } else {
                        dayElem.classList.add("day-unavailable");
                        dayElem.classList.add("flatpickr-disabled");
                    }
                },
                
                onMonthChange: function(selectedDates, dateStr, instance) {
                    // چون تقویم جلالی است، currentYear و currentMonth جلالی هستند
                    // (ماه‌های flatpickr از 0 شروع می‌شوند، جلالی از 1)
                    updateCalendarAvailability(instance.currentYear, instance.currentMonth + 1);
                },
                onYearChange: function(selectedDates, dateStr, instance) {
                     updateCalendarAvailability(instance.currentYear, instance.currentMonth + 1);
                },

                onChange: function(selectedDates, dateStr, instance) {
                    if (selectedDates.length === 0) return;

                    const selectedDate = selectedDates[0];
                    
                    // 1. ثبت تاریخ میلادی در input مخفی (برای ارسال به سرور)
                    const selectedGregorianDate = selectedDate.toISOString().split('T')[0];
                    gregorianDateInput.val(selectedGregorianDate);
                    
                    // 2. نمایش تاریخ شمسی با استفاده از فرمت جلالی
                    const formattedDate = instance.formatDate(selectedDate, "Y/m/d");
                    datePickerInput.val(formattedDate);
                    
                    console.log(`۷. روز ${selectedGregorianDate} (شمسی: ${formattedDate}) انتخاب شد. در حال دریافت اسلات‌ها...`);
                    fetchAndDisplaySlots(selectedGregorianDate);
                }
            });
            // =================================================================
            // *** پایان پیاده‌سازی flatpickr ***
            // =================================================================
            
            datePickerInput.attr('placeholder', 'یک روز را از تقویم بالا انتخاب کنید');
            console.log("۶. تقویم flatpickr-jalali-support با موفقیت ساخته شد.");

        } catch (error) {
            console.error("خطای اساسی در updateCalendarAvailability:", error);
            calendarContainer.html(`<div class="alert alert-danger">خطا در بارگذاری تقویم: ${error.message}</div>`);
            datePickerInput.attr('placeholder', 'خطا در بارگذاری تقویم');
        }
    }

    /**
     * [بدون تغییر] تابع دریافت و نمایش اسلات‌های خالی (ساعت‌ها)
     */
    async function fetchAndDisplaySlots(selectedDate) {
        const totalDuration = totalDurationInput.val();
        
        confirmBtn.prop('disabled', true);
        slotsContainer.html('');
        selectedSlotInput.val('');

        let service_ids = [];
        $('.service-item:checked').each(function() {
            service_ids.push($(this).val());
        });

        if (!totalDuration || !selectedDate || totalDuration == 0 || service_ids.length === 0) return;

        slotsContainer.html('<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>');
        
        const serviceParams = service_ids.map(id => `service_ids[]=${id}`).join('&');
        const deviceId = selectedDeviceInput.val() || '';

        try {
            const url = `${GET_SLOTS_URL}?date=${selectedDate}&total_duration=${totalDuration}&${serviceParams}&device_id=${deviceId}`;

            const response = await fetch(url);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("خطای سرور در دریافت اسلات‌ها:", errorText);
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.error) {
                        throw new Error(errorJson.error); 
                    }
                } catch(e) {
                     throw new Error(`خطای سرور: ${response.status}`);
                }
            }
            const data = await response.json();
            
            slotsContainer.html('<h5 class="text-muted mb-3">۴. انتخاب ساعت:</h5>');
            if (data.available_slots && data.available_slots.length > 0) {
                const slotsGrid = $('<div class="d-flex flex-wrap gap-2"></div>');
                
                data.available_slots.forEach(slot => {
                    const button = $(`<button type="button" class="btn btn-outline-primary" data-slot="${selectedDate} ${slot}">${slot}</button>`);
                    
                    button.on('click', function() {
                        slotsContainer.find('button').removeClass('active'); 
                        $(this).addClass('active'); 
                        selectedSlotInput.val($(this).data('slot')); 
                        confirmBtn.prop('disabled', false);
                    });
                    slotsGrid.append(button);
                });
                slotsContainer.append(slotsGrid);
            } else {
                slotsContainer.append('<div class="alert alert-warning">متاسفانه در این روز با توجه به خدمات انتخابی، زمان خالی وجود ندارد.</div>');
            }
        } catch (error) {
            console.error("Error fetching slots:", error);
            slotsContainer.html(`<div class="alert alert-danger">خطا در دریافت ساعت‌های موجود: ${error.message}</div>`);
        }
    }

    // --- رویداد انتخاب گروه خدمت ---
    serviceGroupSelect.on('change', async function() {
        console.log("گروه خدمت عوض شد.");
        // ریست کردن همه‌چیز
        servicesContainer.html('');
        devicesContainer.html('');
        selectedDeviceInput.val(''); 
        slotsContainer.html('');
        gregorianDateInput.val('');
        
        datePickerInput.val('').attr('placeholder', 'لطفاً ابتدا خدمت را انتخاب کنید...');
        if(calendarInstance) calendarInstance.destroy(); 
        calendarInstance = null;
        calendarContainer.html('<div class="alert alert-info">لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.</div>');
        
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
            console.log("در حال فراخوانی API خدمات:", apiUrl); 
            
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorText = await response.text();
                console.error("خطا در بارگذاری خدمات:", errorText);
                throw new Error(`خطای سرور: ${response.status}`);
            }
            const data = await response.json();
            
            allowMultipleSelection = data.allow_multiple_selection;
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
                    <label for="deviceSelect" class="form-label fs-5">انتخاب دستگاه:</label>
                    <select id="deviceSelect" class="form-select form-select-lg" required>
                        <option value="">--- انتخاب کنید ---</option>
                `;
                devices.forEach(d => {
                    html += `<option value="${d.id}">${d.name}</option>`;
                });
                html += '</select>';
                devicesContainer.html(html);
            } else if (hasDevices) {
                devicesContainer.html('<div class="alert alert-danger">این گروه خدماتی نیاز به دستگاه دارد، اما هیچ دستگاهی برای آن تنظیم نشده است.</div>');
            }
        } catch (error) {
            console.error("خطا در بارگذاری خدمات:", error);
            servicesContainer.html(`<div class="alert alert-danger">خطا در بارگذاری خدمات: ${error.message}</div>`);
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

        gregorianDateInput.val('');
        datePickerInput.val(''); 
        slotsContainer.html('');
        confirmBtn.prop('disabled', true);
        
        console.log("در حال گرفتن تاریخ امروز (شمسی)...");
        // این بخش به persian-date.js متکی است
        const today = new persianDate();
        
        // فراخوانی با سال و ماه جلالی
        updateCalendarAvailability(today.year(), today.month());
    });
    
    /**
     * رویداد انتخاب دستگاه
     */
    $(document).on('change', '#deviceSelect', function() {
        selectedDeviceInput.val($(this).val());
        console.log("دستگاه عوض شد.");

        gregorianDateInput.val('');
        datePickerInput.val(''); 
        slotsContainer.html('');
        confirmBtn.prop('disabled', true);
        
        const today = new persianDate(); 
        // فراخوانی با سال و ماه جلالی
        updateCalendarAvailability(today.year(), today.month());
    });

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
    calendarContainer.html('<div class="alert alert-info">لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.</div>');
    datePickerInput.attr('placeholder', 'لطفاً ابتدا خدمت را انتخاب کنید...');
});