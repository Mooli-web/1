// static/js/booking-api.js
// وظیفه: شامل تمام توابع مربوط به ارتباط با سرور (Fetch/AJAX).

(function(App) {
    // ماژول API
    const api = App.api;
    const ui = App.ui;
    const state = App.state;
    const uiHelpers = App.uiHelpers;

    /**
     * دریافت خدمات و دستگاه‌ها بر اساس گروه خدماتی
     */
    api.fetchServicesForGroup = async function() {
        console.log("گروه خدمت عوض شد.");
        uiHelpers.resetUIOnGroupChange();
        
        const groupId = $(this).val();
        if (!groupId) return;

        ui.servicesContainer.html('<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>');
        
        try {
            const apiUrl = `${state.GET_SERVICES_URL}?group_id=${groupId}`;
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('خطا در بارگذاری خدمات');
            
            const data = await response.json();
            ui.slotsContainer.show();
            
            // رندر کردن خدمات
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
                ui.servicesContainer.html(html);
            } else {
                ui.servicesContainer.html('<div class="alert alert-warning">خدمتی (زیرگروهی) برای این گروه یافت نشد.</div>');
            }
            
            // رندر کردن دستگاه‌ها
            if (data.has_devices && data.devices && data.devices.length > 0) {
                let html = `
                    <label for="deviceSelect" class="form-label fs-5 mt-3">۳. انتخاب دستگاه:</label>
                    <select id="deviceSelect" class="form-select form-select-lg" required>
                        <option value="">--- انتخاب کنید ---</option>
                `;
                data.devices.forEach(d => {
                    html += `<option value="${d.id}">${d.name}</option>`;
                });
                html += '</select>';
                ui.devicesContainer.html(html);
            } else if (data.has_devices) {
                devicesContainer.html('<div class="alert alert-danger">این گروه خدماتی نیاز به دستگاه دارد، اما هیچ دستگاهی برای آن تنظیم نشده است.</div>');
            }
            
        } catch (error) {
            ui.servicesContainer.html(`<div class="alert alert-danger">${error.message}</div>`);
        }
    };

    /**
     * تابع اصلی دریافت اسلات‌ها و نمایش تقویم
     */
    api.fetchAndDisplaySlots = async function() {
        console.log("خدمت یا دستگاه عوض شد.");
        uiHelpers.showSlotsLoading();

        let service_ids = [];
        $('.service-item:checked').each(function() { service_ids.push($(this).val()); });
        const deviceId = ui.selectedDeviceInput.val() || '';
        const hasRequiredDevice = $('#deviceSelect').length > 0;

        if (service_ids.length === 0 || (hasRequiredDevice && !deviceId)) {
            let msg = service_ids.length === 0 ? 'لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.' : 'لطفاً دستگاه مورد نظر را انتخاب کنید.';
            ui.slotsInitialMessage.text(msg).show();
            ui.slotsLoader.hide();
            return;
        }

        const params = new URLSearchParams();
        service_ids.forEach(id => params.append('service_ids[]', id));
        if (deviceId) params.append('device_id', deviceId);
        const apiUrl = `${state.GET_SLOTS_URL}?${params.toString()}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('خطا در دریافت اطلاعات از سرور');
            const slots = await response.json();

            ui.slotsLoader.hide();

            if (slots.length === 0) {
                ui.slotsInitialMessage.text('متاسفانه هیچ زمان خالی در ۳۰ روز آینده یافت نشد.').show();
                return;
            }
            
            const firstSlot = slots[0];
            
            // ==========================================================
            // --- DEBUG 3 ---
            // بیایید ببینیم اولین اسلاتی که از بک‌اند آمده چیست
            // اینجا باید رشته فارسی «آبان» را ببینیم
            console.log("DEBUG (booking-api.js): اولین اسلات دریافتی از سرور:", firstSlot);
            // ==========================================================

            // --- *** شروع اصلاحیه (مشکل شماره ۱) *** ---
            // دیگر نیازی به فرمت کردن با moment نیست
            // رشته‌ی آماده را مستقیماً از API می‌خوانیم
            const readableTime = firstSlot.readable_start;
            // --- *** پایان اصلاحیه (مشکل شماره ۱) *** ---

            ui.firstSlotLabel.text(readableTime);
            ui.bookFirstSlotBtn.data('slot-backend-format', firstSlot.start);
            ui.bookFirstSlotBtn.data('slot-readable', readableTime);
            ui.firstAvailableContainer.removeClass('d-none');

            state.allGroupedSlots = slots.reduce((acc, slot) => {
                const jDate = moment.parseZone(slot.start); // <-- *** اصلاح شد ***
                // کلید ماشینی (jYYYY-jMM-jDD) همچنان برای رندر تقویم استفاده می‌شود
                const dateKey = jDate.format('jYYYY-jMM-jDD'); 
                if (!acc[dateKey]) acc[dateKey] = [];
                acc[dateKey].push(slot);
                return acc;
            }, {});

            const stepLabel = ui.devicesContainer.is(':empty') ? '۳' : '۴';
            ui.calendarStepLabel.text(`${stepLabel}. انتخاب روز و ساعت:`);

            state.currentCalendarMoment = state.todayMoment.clone().startOf('jMonth'); // <-- *** اصلاح شد ***
            
            // ==========================================================
            // --- DEBUG 4 ---
            // اینجا متغیری است که به تقویم ارسال می‌شود تا ماه را رندر کند
            // این باید «آبان» باشد، اما در سیستم شما «بهمن» است
            console.log("DEBUG (booking-api.js): متغیر 'state.currentCalendarMoment' (برای رندر تقویم) تنظیم شد:");
            console.log("DEBUG: فرمت میلادی:", state.currentCalendarMoment.format('YYYY-MM-DD'));
            console.log("DEBUG: فرمت شمسی:", state.currentCalendarMoment.format('jYYYY-jMM-jDD'));
            // ==========================================================

            // فراخوانی buildCalendar (بدون تغییر)
            buildCalendar(state.currentCalendarMoment, state.allGroupedSlots, state.todayMoment); // <-- *** اصلاح شد ***
            
            ui.calendarWrapper.show();

        } catch (error) {
            console.error('Error fetching slots:', error);
            ui.slotsInitialMessage.html(`<div class="alert alert-danger">خطا در بارگذاری زمان‌ها: ${error.message}</div>`).show();
        }
    };

    /**
     * اعتبارسنجی و اعمال کد تخفیف
     */
    api.applyDiscount = async function() {
        const code = ui.discountCodeInput.val();
        const currentBasePrice = parseFloat(ui.basePriceInput.val() || 0);
        
        if (!code || currentBasePrice === 0) {
            ui.discountMessage.text('لطفاً ابتدا خدمت و کد را وارد کنید.').removeClass('text-success').addClass('text-danger');
            return;
        }

        const formData = new FormData();
        formData.append('code', code);
        formData.append('total_price', currentBasePrice);
        formData.append('csrfmiddlewaretoken', state.CSRF_TOKEN);
        
        try {
            const response = await fetch(state.APPLY_DISCOUNT_URL, { method: 'POST', body: formData });
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
                state.codeDiscountAmount = parseFloat(data.discount_amount);
                ui.discountMessage.text(`تخفیف ${parseInt(data.discount_amount).toLocaleString('fa-IR')} تومانی اعمال شد.`).removeClass('text-danger').addClass('text-success');
            }
        } catch (error) {
            console.error("Error applying discount:", error);
            state.codeDiscountAmount = 0; 
            ui.discountMessage.text(error.message).removeClass('text-success').addClass('text-danger');
        }
        
        uiHelpers.updateFinalPrice();
    };

})(window.BookingApp);