// static/js/booking-ui.js
// وظیفه: شامل تمام توابع کمکی مربوط به دستکاری DOM و UI.
// (مانند محاسبه قیمت، مدیریت تایمر، رندر کردن دکمه‌های ساعت)

(function(App) {
    // ماژول کمکی UI
    const uiHelpers = App.uiHelpers;
    const ui = App.ui;
    const state = App.state;

    /**
     * ریست کردن UI هنگام تغییر گروه خدماتی
     */
    uiHelpers.resetUIOnGroupChange = function() {
        ui.servicesContainer.html('');
        ui.devicesContainer.html('');
        ui.selectedDeviceInput.val(''); 
        ui.slotsContainer.hide();
        ui.slotsInitialMessage.text('لطفاً ابتدا خدمت و دستگاه (در صورت نیاز) را انتخاب کنید.').show();
        ui.timeSelectionContainer.html('').hide();
        ui.fomoTimerMessage.hide();
        ui.firstAvailableContainer.addClass('d-none');
        ui.selectedSlotInput.val('');
        ui.confirmBtn.prop('disabled', true);
        ui.basePriceInput.val(0);
        ui.totalDurationInput.val(0);
        state.codeDiscountAmount = 0;
        ui.discountCodeInput.val('');
        ui.discountMessage.text('').removeClass('text-success text-danger');
        uiHelpers.updateFinalPrice();
        state.allGroupedSlots = {};
    };

    /**
     * نمایش لودر هنگام جستجوی اسلات‌ها
     */
    uiHelpers.showSlotsLoading = function() {
        ui.slotsLoader.show();
        ui.slotsInitialMessage.hide();
        ui.calendarWrapper.hide();
        ui.timeSelectionContainer.html('').hide();
        ui.firstAvailableContainer.addClass('d-none');
        ui.confirmBtn.prop('disabled', true);
        ui.selectedSlotInput.val('');
        uiHelpers.stopFomoTimer();
    };

    /**
     * محاسبه و نمایش قیمت نهایی
     */
    uiHelpers.updateFinalPrice = function() {
        let basePrice = parseFloat(ui.basePriceInput.val() || 0);
        let pointsDiscount = 0;
        
        if (ui.applyPointsCheckbox && ui.applyPointsCheckbox.is(':checked')) {
            let maxPointsDiscount = state.MAX_DISCOUNT;
            pointsDiscount = Math.min(basePrice, maxPointsDiscount);
        }
        
        let priceAfterDiscounts = basePrice - pointsDiscount - state.codeDiscountAmount;
        let finalPrice = Math.max(0, priceAfterDiscounts);
        
        ui.finalPriceSpan.text(finalPrice.toLocaleString('fa-IR') + ' تومان');
        
        // به‌روزرسانی لیبل تخفیف امتیاز
        if (ui.applyPointsCheckbox.length) {
            let maxPointsDiscount = state.MAX_DISCOUNT;
            let applicableDiscount = Math.min(basePrice, maxPointsDiscount);
            ui.applyPointsCheckbox.next('label').find('strong').last().text(applicableDiscount.toLocaleString('fa-IR') + ' تومان');
        }
    };

    /**
     * رندر کردن دکمه‌های انتخاب ساعت برای یک روز خاص
     */
    uiHelpers.renderTimeSlots = function(slotsForDay) {
        uiHelpers.stopFomoTimer();
        ui.selectedSlotInput.val('');
        ui.confirmBtn.prop('disabled', true);

        const stepLabel = ui.devicesContainer.is(':empty') ? '۴' : '۵';
        ui.timeSelectionContainer.html(`<label class="form-label fs-5">${stepLabel}. انتخاب ساعت:</label>`);
        
        const buttonGroup = $('<div class="d-flex flex-wrap gap-2 mb-3"></div>');
        
        slotsForDay.forEach(slot => {
            const slotMoment = jalaliMoment.parseZone(slot.start);
            const timeStr = slotMoment.format('HH:mm');
            const backendFormat = slot.start;
            let popularTag = '';
            const hour = slotMoment.hour();
            const dayOfWeek = slotMoment.day(); // شنبه=۰

            if ((hour >= 10 && hour < 14) || dayOfWeek === 3 || dayOfWeek === 4) { // چهارشنبه (3) و پنجشنبه (4)
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
        
        ui.timeSelectionContainer.append(buttonGroup);
        ui.timeSelectionContainer.show();
    };

    /**
     * توقف و پاک کردن تایمر FOMO
     */
    uiHelpers.stopFomoTimer = function() {
        if (state.fomoExpirationTimer) clearTimeout(state.fomoExpirationTimer);
        if (state.fomoIntervalTimer) clearInterval(state.fomoIntervalTimer);
        ui.fomoTimerMessage.hide();
    };

    /**
     * شروع تایمر FOMO (رزرو موقت)
     */
    uiHelpers.startFomoTimer = function() {
        uiHelpers.stopFomoTimer(); // ریست کردن تایمر قبلی
        
        let secondsLeft = state.FOMO_DURATION_SECONDS;
        ui.fomoTimerMessage.removeClass('text-success').addClass('text-danger').show();
        
        state.fomoIntervalTimer = setInterval(() => {
            if (secondsLeft <= 0) {
                 clearInterval(state.fomoIntervalTimer);
                 return;
            }
            secondsLeft--;
            const minutes = Math.floor(secondsLeft / 60);
            const seconds = secondsLeft % 60;
            ui.fomoTimerMessage.html(
                `این زمان به مدت <strong class="mx-1">${minutes}:${seconds.toString().padStart(2, '0')}</strong> برای شما رزرو موقت شد ⏳`
            );
        }, 1000);
        
        state.fomoExpirationTimer = setTimeout(() => {
            clearInterval(state.fomoIntervalTimer);
            ui.fomoTimerMessage.text("!زمان شما منقضی شد. لطفاً مجدداً انتخاب کنید");
            $('.time-select-item').removeClass('active');
            ui.selectedSlotInput.val('');
            ui.confirmBtn.prop('disabled', true);
            setTimeout(() => { ui.fomoTimerMessage.fadeOut(); }, 3000);
        }, state.FOMO_DURATION_SECONDS * 1000);
    };

})(window.BookingApp);