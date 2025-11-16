// static/js/booking-init.js
// وظیفه: فایل راه‌انداز (Initializer) برنامه.
// 1. کتابخانه‌ها را چک می‌کند.
// 2. سلکتورها و متغیرها را از DOM مقداردهی می‌کند.
// 3. Event Listeners را به توابع مناسب متصل می‌کند.

(function(App, $) {
    // ماژول Init
    const init = App.init;
    const ui = App.ui;
    const state = App.state;
    const api = App.api;
    const uiHelpers = App.uiHelpers;

    $(document).ready(function() {
        
        // --- ۱. بررسی کتابخانه‌های ضروری ---
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
        console.log("BookingApp v1.0 (Refactored) لود شد.");

        // --- ۲. مقداردهی سلکتورهای UI ---
        ui.bookingForm = $('#bookingForm');
        ui.serviceGroupSelect = $('#serviceGroup');
        ui.servicesContainer = $('#servicesContainer');
        ui.devicesContainer = $('#devicesContainer');
        ui.selectedDeviceInput = $('#selectedDevice');
        ui.slotsContainer = $('#slotsContainer');
        ui.calendarStepLabel = $('#calendar-step-label');
        ui.calendarWrapper = $('#booking-calendar-wrapper');
        ui.calendarGridBody = $('#calendar-grid-body');
        ui.calendarMonthLabel = $('#calendar-month-label');
        ui.prevMonthBtn = $('#calendar-prev-month');
        ui.nextMonthBtn = $('#calendar-next-month');
        ui.timeSelectionContainer = $('#time-selection-container');
        ui.slotsLoader = $('#slots-loader');
        ui.slotsInitialMessage = $('#slots-initial-message');
        ui.firstAvailableContainer = $('#first-available-slot-container');
        ui.firstSlotLabel = $('#first-slot-label');
        ui.bookFirstSlotBtn = $('#book-first-slot-btn');
        ui.fomoTimerMessage = $('#fomo-timer-message');
        ui.selectedSlotInput = $('#selectedSlot');
        ui.confirmBtn = $('#confirmBtn');
        ui.submitBtn = $('#submitBtn'); // (این دکمه در مودال است، باید بعدا پیدا شود)
        ui.applyPointsCheckbox = $('#apply_points');
        ui.finalPriceSpan = $('#finalPrice');
        ui.confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
        ui.infoConfirmationCheck = $('#infoConfirmationCheck'); // (این چک‌باکس در مودال است)
        ui.discountCodeInput = $('#discountCode');
        ui.applyDiscountBtn = $('#applyDiscountBtn');
        ui.discountMessage = $('#discountMessage');
        ui.basePriceInput = $('#basePrice');
        ui.totalDurationInput = $('#totalDuration');

        // --- ۳. مقداردهی State از DOM (data- attributes) ---
        state.GET_SLOTS_URL = ui.bookingForm.data('get-slots-url');
        state.GET_SERVICES_URL = ui.bookingForm.data('get-services-url');
        state.APPLY_DISCOUNT_URL = ui.bookingForm.data('apply-discount-url');
        state.CSRF_TOKEN = ui.bookingForm.data('csrf-token');
        state.MAX_DISCOUNT = parseFloat(ui.bookingForm.data('max-discount') || 0);
        state.TODAY_DATE_SERVER = ui.bookingForm.data('today-date');

        // (BUG FIX P2) تنظیم "امروز" بر اساس تاریخ سرور
        if (!state.TODAY_DATE_SERVER) {
            console.error("خطای حیاتی: data-today-date یافت نشد. تقویم ممکن است اشتباه باشد.");
            state.todayJalali = jalaliMoment().startOf('day'); // Fallback
        } else {
            state.todayJalali = jalaliMoment(state.TODAY_DATE_SERVER, 'YYYY-MM-DD').startOf('day');
        }

        // --- ۴. اتصال Event Handlers ---

        // انتخاب گروه
        ui.serviceGroupSelect.on('change', api.fetchServicesForGroup);

        // انتخاب خدمت (چون داینامیک اضافه می‌شود از document.on استفاده می‌کنیم)
        $(document).on('change', '.service-item', function() {
            let currentBasePrice = 0;
            let currentTotalDuration = 0;
            $('.service-item:checked').each(function() {
                currentBasePrice += parseFloat($(this).data('price'));
                currentTotalDuration += parseFloat($(this).data('duration'));
            });
            ui.basePriceInput.val(currentBasePrice);
            ui.totalDurationInput.val(currentTotalDuration);
            state.codeDiscountAmount = 0;
            ui.discountCodeInput.val('');
            ui.discountMessage.text('').removeClass('text-success text-danger');
            uiHelpers.updateFinalPrice();
            
            // فراخوانی API
            api.fetchAndDisplaySlots();
        });

        // انتخاب دستگاه
        $(document).on('change', '#deviceSelect', function() {
            ui.selectedDeviceInput.val($(this).val());
            api.fetchAndDisplaySlots();
        });

        // --- رویدادهای تقویم ---
        ui.nextMonthBtn.on('click', function() {
            state.currentCalendarMoment.add(1, 'jMonth');
            buildCalendar(state.currentCalendarMoment, state.allGroupedSlots, state.todayJalali);
        });
        ui.prevMonthBtn.on('click', function() {
            state.currentCalendarMoment.subtract(1, 'jMonth');
            buildCalendar(state.currentCalendarMoment, state.allGroupedSlots, state.todayJalali);
        });
        $(document).on('click', '.calendar-day.available', function(e) {
            e.preventDefault();
            $('.calendar-day').removeClass('selected');
            $(this).addClass('selected');
            const slotsForDay = $(this).data('slots');
            uiHelpers.renderTimeSlots(slotsForDay);
        });

        // --- رویدادهای انتخاب ساعت ---
        $(document).on('click', '.time-select-item', function() {
            $('.time-select-item').removeClass('active');
            $(this).addClass('active');
            ui.selectedSlotInput.val($(this).data('slot-backend-format'));
            ui.confirmBtn.prop('disabled', false);
            uiHelpers.startFomoTimer();
        });
        
        $(document).on('click', '#book-first-slot-btn', function() {
            const selectedSlotValue = $(this).data('slot-backend-format');
            const readableTime = $(this).data('slot-readable');
            ui.selectedSlotInput.val(selectedSlotValue);
            ui.confirmBtn.prop('disabled', false);
            $('.calendar-day').removeClass('selected');
            ui.timeSelectionContainer.html(`<div class="alert alert-success">زمان ${readableTime} انتخاب شد.</div>`).show();
            uiHelpers.stopFomoTimer();
            $('html, body').animate({ scrollTop: $("#confirmBtn").offset().top }, 500);
        });


        // --- رویدادهای تخفیف و ثبت نهایی ---
        if (ui.applyPointsCheckbox.length) {
            ui.applyPointsCheckbox.on('change', uiHelpers.updateFinalPrice);
        }
        ui.applyDiscountBtn.on('click', api.applyDiscount);

        ui.confirmBtn.on('click', function() {
            uiHelpers.stopFomoTimer();
            ui.fomoTimerMessage.text("زمان شما با موفقیت ثبت موقت شد.").removeClass('text-danger').addClass('text-success').show();
            
            // اعتبارسنجی نهایی
            const deviceSelect = $('#deviceSelect');
            if (deviceSelect.length > 0 && !ui.selectedDeviceInput.val()) {
                 alert('لطفا دستگاه مورد نظر را انتخاب کنید.');
                 deviceSelect.focus();
                 return;
            }
            if (ui.bookingForm[0].checkValidity() && $('.service-item:checked').length > 0 && ui.selectedSlotInput.val()) {
                if ($('#manual_confirm').is(':checked')) {
                    ui.bookingForm.submit(); // ثبت دستی توسط پذیرش
                } else {
                    ui.confirmationModal.show(); // نمایش مودال تایید
                }
            } else {
                ui.bookingForm[0].reportValidity();
                if ($('.service-item:checked').length === 0) alert('لطفا حداقل یک خدمت را انتخاب کنید.');
                if (!ui.selectedSlotInput.val()) alert('لطفا زمان نوبت را انتخاب کنید.');
            }
        });

        // (این رویدادها مربوط به داخل مودال هستند)
        $(document).on('change', '#infoConfirmationCheck', function() {
            $('#submitBtn').prop('disabled', !this.checked);
        });
        $(document).on('click', '#submitBtn', function() {
            ui.bookingForm.submit();
        });
        
        // --- ۵. اجرای اولیه ---
        uiHelpers.updateFinalPrice();
    });

})(window.BookingApp, jQuery);