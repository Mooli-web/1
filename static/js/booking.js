// static/js/booking.js
// --- نسخه v5.0 (صفحه‌بندی هفتگی) ---

$(window).on('load', function() {
    console.log("booking.js v5.0 (Weekly Pagination) لود شد.");

    // --- سلکتورهای اصلی (بدون تغییر) ---
    const bookingForm = $('#bookingForm');
    const GET_SLOTS_URL = bookingForm.attr('data-get-slots-url');
    const GET_SERVICES_URL = bookingForm.attr('data-get-services-url');
    const APPLY_DISCOUNT_URL = bookingForm.attr('data-apply-discount-url');
    const CSRF_TOKEN = bookingForm.attr('data-csrf-token');
    const MAX_DISCOUNT = parseFloat(bookingForm.attr('data-max-discount') || 0);

    const serviceGroupSelect = $('#serviceGroup');
    const servicesContainer = $('#servicesContainer');
    const devicesContainer = $('#devicesContainer');
    const selectedDeviceInput = $('#selectedDevice');
    
    // --- سلکتورهای اسلات (و صفحه‌بندی) ---
    const slotsContainer = $('#slotsContainer');
    const daySelectionList = $('#day-selection-list'); // (جدید) محفظه لیست روزها
    const timeSelectionContainer = $('#time-selection-container'); // (جدید) محفظه لیست ساعت‌ها
    const paginationContainer = $('#week-pagination-container'); // (جدید)
    const prevWeekBtn = $('#prevWeekBtn'); // (جدید)
    const nextWeekBtn = $('#nextWeekBtn'); // (جدید)
    const weekLabel = $('#week-label'); // (جدید)

    const selectedSlotInput = $('#selectedSlot');
    const confirmBtn = $('#confirmBtn');
    
    // --- سایر سلکتورها (بدون تغییر) ---
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

    // --- (جدید) متغیرهای سراسری برای صفحه‌بندی ---
    let allGroupedSlots = {}; // برای نگهداری دیتای کامل ۳۰ روزه
    let allDateKeys = []; // کلیدهای تاریخ (برای برش زدن)
    let currentWeek = 0; // هفته جاری (شروع از ۰)
    const DAYS_PER_WEEK = 7;
    paginationContainer.hide();
    // ====================================================================
    // --- ۱. توابع کمکی اصلی (محاسبه قیمت و ...) (بدون تغییر) ---
    // ====================================================================
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
    
    // ====================================================================
    // --- ۲. (جدید) توابع رندر و دریافت اسلات‌ها ---
    // ====================================================================

    /**
     * (جدید) تابع رندر هفته جاری
     * این تابع دیتای از قبل گرفته شده را فقط نمایش می‌دهد
     */
    function renderWeek(weekIndex) {
        // ۱. پاک کردن محتوای قبلی
        daySelectionList.html('');
        timeSelectionContainer.html('').hide();
        selectedSlotInput.val('');
        confirmBtn.prop('disabled', true);

        // ۲. محاسبه روزهای این هفته
        const startIndex = weekIndex * DAYS_PER_WEEK;
        const endIndex = startIndex + DAYS_PER_WEEK;
        const keysForThisWeek = allDateKeys.slice(startIndex, endIndex);

        if (keysForThisWeek.length === 0) {
            daySelectionList.html('<div class="alert alert-secondary">اسلاتی برای این هفته یافت نشد.</div>');
        }

        // ۳. رندر کردن آیتم‌های روز (منطق هوشمند ازدحام)
        keysForThisWeek.forEach(dateKey => {
            const slotsForThisDay = allGroupedSlots[dateKey];
            const count = slotsForThisDay.length;
            let badgeHtml = '';

            if (count <= 3) {
                badgeHtml = `<span class="badge bg-danger ms-2">فقط ${count} اسلات باقی‌مانده</span>`;
            } else if (count <= 7) {
                badgeHtml = `<span class="badge bg-warning text-dark ms-2">ظرفیت محدود</span>`;
            } else {
                badgeHtml = `<span class="badge bg-success ms-2">ظرفیت موجود</span>`;
            }

            const dayItem = $(`
                <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center day-select-item">
                    <strong class="text-primary">${dateKey}</strong>
                    ${badgeHtml}
                </a>
            `);
            dayItem.data('slots', slotsForThisDay); // ذخیره اسلات‌ها در دکمه
            daySelectionList.append(dayItem);
        });

        // ۴. به‌روزرسانی دکمه‌های صفحه‌بندی
        prevWeekBtn.prop('disabled', weekIndex === 0);
        nextWeekBtn.prop('disabled', endIndex >= allDateKeys.length);
        
        // ۵. به‌روزرسانی لیبل هفته
        const totalWeeks = Math.ceil(allDateKeys.length / DAYS_PER_WEEK);
        if (totalWeeks > 1) {
             weekLabel.text(`هفته ${weekIndex + 1} از ${totalWeeks}`);
             paginationContainer.show();
        } else {
            paginationContainer.hide();
        }
    }

    /**
     * (اصلاح‌شده) تابع اصلی برای دریافت همه اسلات‌ها
     * این تابع API را کال می‌کند و دیتای ۳۰ روزه را در متغیرهای سراسری می‌ریزد
     */
    async function fetchAndDisplaySlots() {
        // ۱. نمایش لودینگ
        daySelectionList.html('<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p>در حال جستجوی زمان‌های خالی...</p></div>');
        timeSelectionContainer.html('').hide();
        paginationContainer.hide();
        confirmBtn.prop('disabled', true);
        selectedSlotInput.val('');
        $('label[for="slotsContainer"]').remove(); // حذف لیبل قدیمی

        // ۲. جمع‌آوری پارامترها (بدون تغییر)
        let service_ids = [];
        $('.service-item:checked').each(function() {
            service_ids.push($(this).val());
        });
        const deviceId = selectedDeviceInput.val() || '';
        const hasRequiredDevice = $('#deviceSelect').length > 0;

        // ۳. اعتبارسنجی (بدون تغییر)
        if (service_ids.length === 0 || (hasRequiredDevice && !deviceId)) {
            let msg = service_ids.length === 0 
                ? 'لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.' 
                : 'لطفاً دستگاه مورد نظر را انتخاب کنید.';
            daySelectionList.html(`<div class="alert alert-info">${msg}</div>`);
            return;
        }

        // ۴. ساخت URL و فراخوانی API (بدون تغییر)
        const params = new URLSearchParams();
        service_ids.forEach(id => params.append('service_ids[]', id));
        if (deviceId) {
            params.append('device_id', deviceId);
        }
        const apiUrl = `${GET_SLOTS_URL}?${params.toString()}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('خطا در دریافت اطلاعات از سرور');
            const slots = await response.json();

            if (slots.length === 0) {
                daySelectionList.html('<div class="alert alert-warning">متاسفانه هیچ زمان خالی در ۳۰ روز آینده یافت نشد.</div>');
                return;
            }

            // ۵. (اصلاح‌شده) گروه‌بندی اسلات‌ها و ذخیره در متغیر سراسری
            allGroupedSlots = slots.reduce((acc, slot) => {
                const slotDate = new Date(slot.start);
                const dateKey = slotDate.toLocaleDateString('fa-IR', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long'
                });
                if (!acc[dateKey]) acc[dateKey] = [];
                acc[dateKey].push(slot);
                return acc;
            }, {});

            allDateKeys = Object.keys(allGroupedSlots); // ذخیره کلیدها
            currentWeek = 0; // ریست کردن هفته

            // ۶. (جدید) افزودن لیبل اصلی (مرحله ۳: انتخاب روز)
            const stepLabel = devicesContainer.is(':empty') ? '۳' : '۴';
            slotsContainer.prepend(`<label class_form-label fs-5 mb-3" for="slotsContainer">${stepLabel}. انتخاب روز:</label>`);

            // ۷. (جدید) رندر کردن هفته اول
            renderWeek(currentWeek);

        } catch (error) {
            console.error('Error fetching slots:', error);
            daySelectionList.html(`<div class="alert alert-danger">خطا در بارگذاری زمان‌ها: ${error.message}</div>`);
        }
    }

    // ====================================================================
    // --- ۳. رویدادهای مربوط به فرم (انتخاب خدمت، دستگاه و ...) ---
    // ====================================================================

    // --- رویداد انتخاب گروه خدمت ---
    serviceGroupSelect.on('change', async function() {
        console.log("گروه خدمت عوض شد.");
        // ریست کردن همه‌چیز
        servicesContainer.html('');
        devicesContainer.html('');
        selectedDeviceInput.val(''); 
        
        $('label[for="slotsContainer"]').remove(); // حذف لیبل
        daySelectionList.html('<div class="alert alert-info">لطفاً ابتدا خدمت و دستگاه (در صورت نیاز) را انتخاب کنید.</div>');
        timeSelectionContainer.html('').hide();
        paginationContainer.hide();
        
        selectedSlotInput.val('');
        confirmBtn.prop('disabled', true);
        basePriceInput.val(0);
        totalDurationInput.val(0);
        codeDiscountAmount = 0;
        discountCodeInput.val('');
        discountMessage.text('').removeClass('text-success text-danger');
        updateFinalPrice();
        
        // ریست متغیرهای سراسری
        allGroupedSlots = {};
        allDateKeys = [];
        currentWeek = 0;
        
        const groupId = $(this).val();
        if (!groupId) return;

        servicesContainer.html('<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>');

        try {
            // (منطق دریافت خدمات بدون تغییر)
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
                    <label for="deviceSelect" class="form-label fs-5 mt-3">۳. انتخاب دستگاه:</label>
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
        fetchAndDisplaySlots(); // فراخوانی تابع اصلی
    });
    
    /**
     * رویداد انتخاب دستگاه
     */
    $(document).on('change', '#deviceSelect', function() {
        selectedDeviceInput.val($(this).val());
        console.log("دستگاه عوض شد.");
        fetchAndDisplaySlots(); // فراخوانی تابع اصلی
    });

    // ====================================================================
    // --- ۴. رویدادهای کلیک دو مرحله‌ای و صفحه‌بندی ---
    // ====================================================================

    /**
     * (جدید) رویداد کلیک دکمه‌های صفحه‌بندی
     */
    nextWeekBtn.on('click', function() {
        const totalWeeks = Math.ceil(allDateKeys.length / DAYS_PER_WEEK);
        if (currentWeek < totalWeeks - 1) {
            currentWeek++;
            renderWeek(currentWeek);
        }
    });

    prevWeekBtn.on('click', function() {
        if (currentWeek > 0) {
            currentWeek--;
            renderWeek(currentWeek);
        }
    });

    /**
     * رویداد کلیک روی یک روز در لیست روزها
     */
    $(document).on('click', '.day-select-item', function(e) {
        e.preventDefault();
        
        // (منطق این بخش بدون تغییر است)
        $('.day-select-item').removeClass('active');
        $(this).addClass('active');
        selectedSlotInput.val('');
        confirmBtn.prop('disabled', true);

        const slotsForDay = $(this).data('slots');
        
        // (جدید) لیبل مرحله انتخاب ساعت
        const stepLabel = devicesContainer.is(':empty') ? '۴' : '۵';
        timeSelectionContainer.html(`<label class="form-label fs-5">${stepLabel}. انتخاب ساعت:</label>`);
        
        const buttonGroup = $('<div class="d-flex flex-wrap gap-2 mb-3"></div>');
        slotsForDay.forEach(slot => {
            const slotDate = new Date(slot.start);
            const timeStr = slotDate.toLocaleTimeString('fa-IR', { 
                hour: '2-digit', 
                minute: '2-digit', 
                hour12: false,
                timeZone: 'Asia/Tehran'
            });
            const d = new Date(slot.start);
            const year = d.getUTCFullYear();
            const month = (d.getUTCMonth() + 1).toString().padStart(2, '0');
            const day = d.getUTCDate().toString().padStart(2, '0');
            const hour = d.getUTCHours().toString().padStart(2, '0');
            const minute = d.getUTCMinutes().toString().padStart(2, '0');
            const backendFormat = `${year}-${month}-${day} ${hour}:${minute}`;
            const button = $(`
                <button type="button" 
                        class="btn btn-outline-primary time-select-item" 
                        data-slot-backend-format="${backendFormat}">
                    ${timeStr}
                </button>
            `);
            buttonGroup.append(button);
        });

        timeSelectionContainer.append(buttonGroup);
        timeSelectionContainer.show();
    });

    /**
     * رویداد کلیک روی دکمه ساعت
     */
    $(document).on('click', '.time-select-item', function() {
        $('.time-select-item').removeClass('active');
        $(this).addClass('active');
        selectedSlotInput.val($(this).data('slot-backend-format'));
        confirmBtn.prop('disabled', false);
    });

    // ====================================================================
    // --- ۵. رویدادهای تخفیف و ثبت نهایی (کاملاً بدون تغییر) ---
    // ====================================================================

    if (applyPointsCheckbox) {
        applyPointsCheckbox.on('change', updateFinalPrice);
    }
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
            const response = await fetch(APPLY_DISCOUNT_URL, { method: 'POST', body: formData });
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