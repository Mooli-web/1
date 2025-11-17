// static/js/booking-api.js
// --- نسخه v7.1 (Refactor Complete: Dumb Frontend) ---
// وظیفه: شامل تمام توابع مربوط به ارتباط با سرور (Fetch/AJAX).
// (این فایل دیگر هیچ پردازش تاریخی انجام نمی‌دهد)

(function(App) {
    // ماژول API
    const api = App.api;
    const ui = App.ui;
    const state = App.state;
    const uiHelpers = App.uiHelpers;

    /**
     * دریافت خدمات و دستگاه‌ها بر اساس گروه خدماتی
     * (بدون تغییر)
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
     * (بازسازی شده برای معماری Smart Backend)
     */
    api.fetchAndDisplaySlots = async function() {
        console.log("خدمت یا دستگاه عوض شد.");
        
        ui.slotsContainer.show();
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
            
            // 'groupedSlots' آبجکت آماده‌ای است که مستقیم از پایتون می‌آید
            // (مثال: {'1404-08-26': [...], '1404-08-27': [...]})
            const groupedSlots = await response.json();

            ui.slotsLoader.hide();

            // بررسی اینکه آیا آبجکت دریافتی خالی است یا خیر
            if (Object.keys(groupedSlots).length === 0) {
                ui.slotsInitialMessage.text('متاسفانه هیچ زمان خالی در ۳۰ روز آینده یافت نشد.').show();
                return;
            }
            
            // --- منطق جدید برای یافتن اولین اسلات ---
            const firstDateKey = Object.keys(groupedSlots)[0];
            const firstSlot = groupedSlots[firstDateKey][0];
            
            const readableTime = firstSlot.readable_start;

            ui.firstSlotLabel.text(readableTime);
            ui.bookFirstSlotBtn.data('slot-backend-format', firstSlot.start);
            ui.bookFirstSlotBtn.data('slot-readable', readableTime);
            ui.firstAvailableContainer.removeClass('d-none');

            // ما آبجکت آماده بک‌اند را مستقیماً به state می‌دهیم.
            state.allGroupedSlots = groupedSlots;
            
            const stepLabel = ui.devicesContainer.is(':empty') ? '۳' : '۴';
            ui.calendarStepLabel.text(`${stepLabel}. انتخاب روز و ساعت:`);

            state.currentCalendarMoment = state.todayMoment.clone().startOf('jMonth');
            
            // فراخوانی buildCalendar
            // اکنون 'state.allGroupedSlots' دقیقاً فرمتی را دارد که 'buildCalendar' انتظار دارد.
            buildCalendar(state.currentCalendarMoment, state.allGroupedSlots, state.todayMoment);
            
            ui.calendarWrapper.show();

        } catch (error) {
            console.error('Error fetching slots:', error);
            ui.slotsInitialMessage.html(`<div class="alert alert-danger">خطا در بارگذاری زمان‌ها: ${error.message}</div>`).show();
        }
    };

    /**
     * اعتبارسنجی و اعمال کد تخفیف
     * (بدون تغییر)
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