// static/js/booking-main.js
// --- نسخه v6.4 (Global Scope Fix) ---
// این فایل "کنترلر" اصلی صفحه رزرو است.

// ====================================================================
// --- ۱. تعریف متغیرهای سراسری (Global Scope) ---
// این متغیرها باید Global باشند تا booking-calendar.js به آنها دسترسی داشته باشد.
// ====================================================================

// --- سلکتورهای اصلی ---
let bookingForm, GET_SLOTS_URL, GET_SERVICES_URL, APPLY_DISCOUNT_URL, CSRF_TOKEN, MAX_DISCOUNT;
let serviceGroupSelect, servicesContainer, devicesContainer, selectedDeviceInput;
let slotsContainer, calendarStepLabel, calendarWrapper, calendarGridBody, calendarMonthLabel, prevMonthBtn, nextMonthBtn;
let timeSelectionContainer, slotsLoader, slotsInitialMessage; // <-- timeSelectionContainer اکنون Global است
let firstAvailableContainer, firstSlotLabel, bookFirstSlotBtn, fomoTimerMessage;
let selectedSlotInput, confirmBtn, submitBtn, applyPointsCheckbox, finalPriceSpan;
let confirmationModal, infoConfirmationCheck, discountCodeInput, applyDiscountBtn, discountMessage;
let basePriceInput, totalDurationInput;
let codeDiscountAmount = 0;

// --- متغیرهای سراسری وضعیت (State) ---
let allGroupedSlots = {}; // دیتای API
let todayJalali = null;
let currentCalendarMoment = null; // ماه جاری

// --- ایده ۴: متغیرهای تایمر FOMO ---
let fomoExpirationTimer = null;
let fomoIntervalTimer = null;
const FOMO_DURATION_SECONDS = 5 * 60; // 5 دقیقه

// ====================================================================
// --- ۲. توابع کمکی (Global Scope) ---
// ====================================================================

/**
 * (بدون تغییر) محاسبه قیمت نهایی
 */
function updateFinalPrice() {
    let basePrice = parseFloat(basePriceInput.val() || 0);
    let pointsDiscount = 0;
    if (applyPointsCheckbox && applyPointsCheckbox.is(':checked')) {
        maxPointsDiscount = MAX_DISCOUNT;
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
 * (نسخه v6.3 - Timezone Fix)
 * تابع اصلی دریافت اسلات‌ها
 */
async function fetchAndDisplaySlots() {
    // ۱. نمایش لودینگ (بدون تغییر)
    slotsLoader.show();
    slotsInitialMessage.hide();
    calendarWrapper.hide();
    timeSelectionContainer.html('').hide();
    firstAvailableContainer.addClass('d-none');
    confirmBtn.prop('disabled', true);
    selectedSlotInput.val('');
    fomoTimerMessage.hide();
    if (fomoExpirationTimer) clearTimeout(fomoExpirationTimer);
    if (fomoIntervalTimer) clearInterval(fomoIntervalTimer);

    // ۲. جمع‌آوری پارامترها (بدون تغییر)
    let service_ids = [];
    $('.service-item:checked').each(function() { service_ids.push($(this).val()); });
    const deviceId = selectedDeviceInput.val() || '';
    const hasRequiredDevice = $('#deviceSelect').length > 0;

    // ۳. اعتبارسنجی (بدون تغییر)
    if (service_ids.length === 0 || (hasRequiredDevice && !deviceId)) {
        let msg = service_ids.length === 0 ? 'لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.' : 'لطفاً دستگاه مورد نظر را انتخاب کنید.';
        slotsInitialMessage.text(msg).show();
        slotsLoader.hide();
        return;
    }

    // ۴. فراخوانی API (بدون تغییر)
    const params = new URLSearchParams();
    service_ids.forEach(id => params.append('service_ids[]', id));
    if (deviceId) params.append('device_id', deviceId);
    const apiUrl = `${GET_SLOTS_URL}?${params.toString()}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error('خطا در دریافت اطلاعات از سرور');
        const slots = await response.json();

        slotsLoader.hide();

        if (slots.length === 0) {
            slotsInitialMessage.text('متاسفانه هیچ زمان خالی در ۳۰ روز آینده یافت نشد.').show();
            return;
        }
        
        // --- ایده ۲: دکمه "اولین نوبت موجود" (بدون تغییر) ---
        const firstSlot = slots[0];
        const readableTime = jalaliMoment.parseZone(firstSlot.start).format('dddd jD jMMMM، ساعت HH:mm');
        firstSlotLabel.text(readableTime);
        bookFirstSlotBtn.data('slot-backend-format', firstSlot.start);
        bookFirstSlotBtn.data('slot-readable', readableTime);
        firstAvailableContainer.removeClass('d-none');

        // ۵. گروه‌بندی اسلات‌ها (Timezone Fix - بدون تغییر)
        allGroupedSlots = slots.reduce((acc, slot) => {
            const jDate = jalaliMoment.parseZone(slot.start);
            const dateKey = jDate.format('jYYYY-jMM-jDD');
            if (!acc[dateKey]) acc[dateKey] = [];
            acc[dateKey].push(slot);
            return acc;
        }, {});

        // ۶. افزودن لیبل اصلی (بدون تغییر)
        const stepLabel = devicesContainer.is(':empty') ? '۳' : '۴';
        calendarStepLabel.text(`${stepLabel}. انتخاب روز و ساعت:`);

        // ۷. رندر کردن تقویم ماه جاری (بدون تغییر)
        todayJalali = jalaliMoment().startOf('day');
        currentCalendarMoment = todayJalali.clone().startOf('jMonth');
        
        // فراخوانی تابع رندر از booking-calendar.js
        // (اکنون buildCalendar به متغیرهای Global دسترسی دارد)
        buildCalendar(currentCalendarMoment, allGroupedSlots, todayJalali);
        calendarWrapper.show();

    } catch (error) {
        console.error('Error fetching slots:', error);
        slotsLoader.hide();
        slotsInitialMessage.html(`<div class="alert alert-danger">خطا در بارگذاری زمان‌ها: ${error.message}</div>`).show();
    }
}

// ====================================================================
// --- ۳. اجرای اصلی (Document Ready) ---
// ====================================================================

/**
 * استفاده از $(document).ready() به جای $(window).on('load', ...)
 * این تابع پس از آماده شدن DOM اجرا می‌شود.
 */
$(document).ready(function() {
    
    // --- اطمینان از بارگذاری کتابخانه‌ها ---
    if (typeof jalaliMoment === 'undefined') {
        console.error("خطای حیاتی: کتابخانه jalali-moment بارگذاری نشده است.");
        alert("خطا در بارگذاری تقویم. لطفاً صفحه را رفرش کنید.");
        return;
    }
    if (typeof buildCalendar === 'undefined') {
        console.error("خطای حیاتی: کتابخانه booking-calendar.js بارگذاری نشده است.");
        return;
    }
    jalaliMoment.locale('fa'); // تنظیم سراسری زبان
    console.log("booking.js v6.4 (Global Scope Fix) لود شد.");


    // --- مقداردهی (Assign) سلکتورهای Global ---
    bookingForm = $('#bookingForm');
    GET_SLOTS_URL = bookingForm.attr('data-get-slots-url');
    GET_SERVICES_URL = bookingForm.attr('data-get-services-url');
    APPLY_DISCOUNT_URL = bookingForm.attr('data-apply-discount-url');
    CSRF_TOKEN = bookingForm.attr('data-csrf-token');
    MAX_DISCOUNT = parseFloat(bookingForm.attr('data-max-discount') || 0);

    serviceGroupSelect = $('#serviceGroup');
    servicesContainer = $('#servicesContainer');
    devicesContainer = $('#devicesContainer');
    selectedDeviceInput = $('#selectedDevice');
    
    slotsContainer = $('#slotsContainer');
    calendarStepLabel = $('#calendar-step-label');
    calendarWrapper = $('#booking-calendar-wrapper');
    calendarGridBody = $('#calendar-grid-body');
    calendarMonthLabel = $('#calendar-month-label');
    prevMonthBtn = $('#calendar-prev-month');
    nextMonthBtn = $('#calendar-next-month');
    timeSelectionContainer = $('#time-selection-container'); // <-- اینجا مقداردهی شد
    slotsLoader = $('#slots-loader');
    slotsInitialMessage = $('#slots-initial-message');
    
    firstAvailableContainer = $('#first-available-slot-container');
    firstSlotLabel = $('#first-slot-label');
    bookFirstSlotBtn = $('#book-first-slot-btn');
    fomoTimerMessage = $('#fomo-timer-message');

    selectedSlotInput = $('#selectedSlot');
    confirmBtn = $('#confirmBtn');
    submitBtn = $('#submitBtn');
    applyPointsCheckbox = $('#apply_points');
    finalPriceSpan = $('#finalPrice');
    confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    infoConfirmationCheck = $('#infoConfirmationCheck');
    discountCodeInput = $('#discountCode');
    applyDiscountBtn = $('#applyDiscountBtn');
    discountMessage = $('#discountMessage');
    basePriceInput = $('#basePrice');
    totalDurationInput = $('#totalDuration');


    // ====================================================================
    // --- ۴. اتصال رویدادها (Event Handlers) ---
    // ====================================================================

    // --- رویداد انتخاب گروه خدمت ---
    serviceGroupSelect.on('change', async function() {
        console.log("گروه خدمت عوض شد.");
        // (این تابع کاملاً مشابه نسخه v6.2 است و نیازی به تغییر ندارد)
        servicesContainer.html('');
        devicesContainer.html('');
        selectedDeviceInput.val(''); 
        slotsContainer.hide();
        slotsInitialMessage.text('لطفاً ابتدا خدمت و دستگاه (در صورت نیاز) را انتخاب کنید.').show();
        timeSelectionContainer.html('').hide();
        fomoTimerMessage.hide();
        firstAvailableContainer.addClass('d-none');
        selectedSlotInput.val('');
        confirmBtn.prop('disabled', true);
        basePriceInput.val(0);
        totalDurationInput.val(0);
        codeDiscountAmount = 0;
        discountCodeInput.val('');
        discountMessage.text('').removeClass('text-success text-danger');
        updateFinalPrice();
        allGroupedSlots = {};
        const groupId = $(this).val();
        if (!groupId) return;
        servicesContainer.html('<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>');
        try {
            const apiUrl = `${GET_SERVICES_URL}?group_id=${groupId}`;
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('خطا در بارگذاری خدمات');
            const data = await response.json();
            slotsContainer.show();
            const hasDevices = data.has_devices;
            const devices = data.devices;
            if (data.services && data.services.length > 0) {
                let html = `<label class="form-label fs-5">۲. انتخاب خدمات:</label><div class="list-group service-list-group">`;
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

    // --- رویداد انتخاب خدمت (بدون تغییر) ---
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
        fetchAndDisplaySlots();
    });
    
    // --- رویداد انتخاب دستگاه (بدون تغییر) ---
    $(document).on('change', '#deviceSelect', function() {
        selectedDeviceInput.val($(this).val());
        console.log("دستگاه عوض شد.");
        fetchAndDisplaySlots();
    });

    // --- رویداد کلیک دکمه‌های ماه قبل/بعد (بدون تغییر) ---
    nextMonthBtn.on('click', function() {
        currentCalendarMoment.add(1, 'jMonth');
        buildCalendar(currentCalendarMoment, allGroupedSlots, todayJalali);
    });
    prevMonthBtn.on('click', function() {
        currentCalendarMoment.subtract(1, 'jMonth');
        buildCalendar(currentCalendarMoment, allGroupedSlots, todayJalali);
    });

    // --- رویداد کلیک دکمه «رزرو فوری» (بدون تغییر) ---
    $(document).on('click', '#book-first-slot-btn', function() {
        const selectedSlotValue = $(this).data('slot-backend-format');
        const readableTime = $(this).data('slot-readable');
        selectedSlotInput.val(selectedSlotValue);
        confirmBtn.prop('disabled', false);
        $('.calendar-day').removeClass('selected');
        timeSelectionContainer.html('').hide();
        fomoTimerMessage.hide();
        if (fomoExpirationTimer) clearTimeout(fomoExpirationTimer);
        if (fomoIntervalTimer) clearInterval(fomoIntervalTimer);
        timeSelectionContainer.html(`<div class="alert alert-success">زمان ${readableTime} انتخاب شد.</div>`).show();
        $('html, body').animate({ scrollTop: $("#confirmBtn").offset().top }, 500);
    });
    
    // --- رویداد کلیک روی "روز" در تقوim (بدون تغییر) ---
    $(document).on('click', '.calendar-day.available', function(e) {
        e.preventDefault();
        
        $('.calendar-day').removeClass('selected');
        $(this).addClass('selected');
        selectedSlotInput.val('');
        confirmBtn.prop('disabled', true);
        fomoTimerMessage.hide();
        if (fomoExpirationTimer) clearTimeout(fomoExpirationTimer);
        if (fomoIntervalTimer) clearInterval(fomoIntervalTimer);

        const slotsForDay = $(this).data('slots');
        const dayDateObject = $(this).data('date-object');
        
        const stepLabel = devicesContainer.is(':empty') ? '۴' : '۵';
        timeSelectionContainer.html(`<label class="form-label fs-5">${stepLabel}. انتخاب ساعت:</label>`);
        
        const buttonGroup = $('<div class="d-flex flex-wrap gap-2 mb-3"></div>');
        
        slotsForDay.forEach(slot => {
            const slotMoment = jalaliMoment.parseZone(slot.start);
            const timeStr = slotMoment.format('HH:mm');
            const backendFormat = slot.start;
            let popularTag = '';
            const hour = slotMoment.hour();
            const dayOfWeek = slotMoment.day(); // شنبه=۰

            // (اصلاحیه) قانون بازاریابی: چهارشنبه (۳) و پنجشنبه (۴)
            if ((hour >= 10 && hour < 14) || dayOfWeek === 3 || dayOfWeek === 4) {
                popularTag = '<span class="popular-tag">🔥 محبوب</span>';
            }
            
            const button = $(`
                <button type="button" 
                        class="btn btn-outline-primary time-select-item" 
                        data-slot-backend-format="${backendFormat}">
                    ${popularTag}${timeStr}
                </button>
            `);
            buttonGroup.append(button);
        });
        timeSelectionContainer.append(buttonGroup);
        timeSelectionContainer.show();
    });

    // --- رویداد کلیک روی "ساعت" (بدون تغییر) ---
    $(document).on('click', '.time-select-item', function() {
        $('.time-select-item').removeClass('active');
        $(this).addClass('active');
        selectedSlotInput.val($(this).data('slot-backend-format'));
        confirmBtn.prop('disabled', false);

        if (fomoExpirationTimer) clearTimeout(fomoExpirationTimer);
        if (fomoIntervalTimer) clearInterval(fomoIntervalTimer);
        let secondsLeft = FOMO_DURATION_SECONDS;
        fomoTimerMessage.removeClass('text-success').addClass('text-danger').show();
        fomoIntervalTimer = setInterval(() => {
            if (secondsLeft <= 0) {
                 clearInterval(fomoIntervalTimer);
                 return;
            }
            secondsLeft--;
            const minutes = Math.floor(secondsLeft / 60);
            const seconds = secondsLeft % 60;
            fomoTimerMessage.html(
                `این زمان به مدت <strong class="mx-1">${minutes}:${seconds.toString().padStart(2, '0')}</strong> برای شما رزرو موقت شد ⏳`
            );
        }, 1000);
        fomoExpirationTimer = setTimeout(() => {
            clearInterval(fomoIntervalTimer);
            fomoTimerMessage.text("!زمان شما منقضی شد. لطفاً مجدداً انتخاب کنید");
            $('.time-select-item').removeClass('active');
            selectedSlotInput.val('');
            confirmBtn.prop('disabled', true);
            setTimeout(() => { fomoTimerMessage.fadeOut(); }, 3000);
        }, FOMO_DURATION_SECONDS * 1000);
    });

    // --- رویدادهای تخفیف و ثبت نهایی (بدون تغییر) ---
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
        if (fomoExpirationTimer) clearTimeout(fomoExpirationTimer);
        if (fomoIntervalTimer) clearInterval(fomoIntervalTimer);
        fomoTimerMessage.text("زمان شما با موفقیت ثبت موقت شد.").removeClass('text-danger').addClass('text-success').show();
        
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