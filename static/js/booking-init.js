// static/js/booking-init.js
// وظیفه: فایل راه‌انداز (Initializer) برنامه.

(function(App, $) {
    const ui = App.ui;
    const state = App.state;
    const api = App.api;
    const uiHelpers = App.uiHelpers;

    $(document).ready(function() {
        
        // --- ۱. بررسی کتابخانه‌های ضروری ---
        if (typeof moment === 'undefined' || typeof moment.fn.jYear === 'undefined') {
            console.error("خطای حیاتی: کتابخانه jalali-moment بارگذاری نشده است.");
            return;
        }
        if (typeof buildCalendar === 'undefined') {
            console.error("خطای حیاتی: کتابخانه booking-calendar.js بارگذاری نشده است.");
            return;
        }

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
        ui.submitBtn = $('#submitBtn'); 
        ui.applyPointsCheckbox = $('#apply_points');
        ui.finalPriceSpan = $('#finalPrice');
        ui.confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
        ui.infoConfirmationCheck = $('#infoConfirmationCheck'); 
        ui.discountCodeInput = $('#discountCode');
        ui.applyDiscountBtn = $('#applyDiscountBtn');
        ui.discountMessage = $('#discountMessage');
        ui.basePriceInput = $('#basePrice');
        ui.totalDurationInput = $('#totalDuration');
        // --- المنت‌های جدید ---
        ui.rewardBox = $('#rewardBox');
        ui.rewardText = $('#rewardText');

        // --- ۳. مقداردهی State از DOM ---
        state.GET_SLOTS_URL = ui.bookingForm.data('get-slots-url');
        state.GET_SERVICES_URL = ui.bookingForm.data('get-services-url');
        state.APPLY_DISCOUNT_URL = ui.bookingForm.data('apply-discount-url');
        state.CSRF_TOKEN = ui.bookingForm.data('csrf-token');
        state.MAX_DISCOUNT = parseFloat(ui.bookingForm.data('max-discount') || 0);
        state.TODAY_DATE_SERVER = ui.bookingForm.data('today-date');
        // --- خواندن نرخ امتیاز ---
        state.PRICE_TO_POINTS_RATE = parseFloat(ui.bookingForm.data('points-rate') || 0);

        if (!state.TODAY_DATE_SERVER) {
            state.todayMoment = moment().startOf('day');
        } else {
            state.todayMoment = moment(state.TODAY_DATE_SERVER, 'YYYY-MM-DD').startOf('day');
        }
        moment.locale('fa'); 

        // --- ۴. اتصال Event Handlers ---
        ui.serviceGroupSelect.on('change', api.fetchServicesForGroup);

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
            uiHelpers.updateFinalPrice(); // <-- محاسبه پاداش اینجا انجام می‌شود
            api.fetchAndDisplaySlots();
        });

        $(document).on('change', '#deviceSelect', function() {
            ui.selectedDeviceInput.val($(this).val());
            api.fetchAndDisplaySlots();
        });

        ui.nextMonthBtn.on('click', function() {
            state.currentCalendarMoment.add(1, 'jMonth');
            buildCalendar(state.currentCalendarMoment, state.allGroupedSlots, state.todayMoment); 
        });
        ui.prevMonthBtn.on('click', function() {
            state.currentCalendarMoment.subtract(1, 'jMonth');
            buildCalendar(state.currentCalendarMoment, state.allGroupedSlots, state.todayMoment); 
        });
        $(document).on('click', '.calendar-day.available', function(e) {
            e.preventDefault();
            $('.calendar-day').removeClass('selected');
            $(this).addClass('selected');
            const slotsForDay = $(this).data('slots');
            uiHelpers.renderTimeSlots(slotsForDay);
        });

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

        if (ui.applyPointsCheckbox.length) {
            ui.applyPointsCheckbox.on('change', uiHelpers.updateFinalPrice);
        }
        ui.applyDiscountBtn.on('click', api.applyDiscount);

        ui.confirmBtn.on('click', function() {
            uiHelpers.stopFomoTimer();
            ui.fomoTimerMessage.text("زمان شما با موفقیت ثبت موقت شد.").removeClass('text-danger').addClass('text-success').show();
            
            const deviceSelect = $('#deviceSelect');
            if (deviceSelect.length > 0 && !ui.selectedDeviceInput.val()) {
                 alert('لطفا دستگاه مورد نظر را انتخاب کنید.');
                 deviceSelect.focus();
                 return;
            }
            if (ui.bookingForm[0].checkValidity() && $('.service-item:checked').length > 0 && ui.selectedSlotInput.val()) {
                if ($('#manual_confirm').is(':checked')) {
                    ui.bookingForm.submit(); 
                } else {
                    ui.confirmationModal.show(); 
                }
            } else {
                ui.bookingForm[0].reportValidity();
                if ($('.service-item:checked').length === 0) alert('لطفا حداقل یک خدمت را انتخاب کنید.');
                if (!ui.selectedSlotInput.val()) alert('لطفا زمان نوبت را انتخاب کنید.');
            }
        });

        $(document).on('change', '#infoConfirmationCheck', function() {
            $('#submitBtn').prop('disabled', !this.checked);
        });
        $(document).on('click', '#submitBtn', function() {
            ui.bookingForm.submit();
        });
        
        uiHelpers.updateFinalPrice();
    });

})(window.BookingApp, jQuery);