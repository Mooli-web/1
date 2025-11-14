// static/js/booking.js
// --- اصلاحیه: استفاده از (window).on('load') به جای (document).ready
// --- این کار تضمین می‌کند که اسکریپت‌های خارجی (پلاگین‌ها) قبل از اجرای این کد، لود شده‌اند.

$(window).on('load', function() {
    console.log("booking.js v2.0 (FullCalendar) لود شد. (در حالت Window Load)");

    // --- خواندن data attributes از فرم ---
    const bookingForm = $('#bookingForm');
    const GET_SLOTS_URL = bookingForm.attr('data-get-slots-url'); // <-- API جدید
    const GET_SERVICES_URL = bookingForm.attr('data-get-services-url');
    const APPLY_DISCOUNT_URL = bookingForm.attr('data-apply-discount-url');
    const CSRF_TOKEN = bookingForm.attr('data-csrf-token');
    const MAX_DISCOUNT = parseFloat(bookingForm.attr('data-max-discount') || 0);

    // --- سلکتورهای اصلی ---
    const serviceGroupSelect = $('#serviceGroup');
    const servicesContainer = $('#servicesContainer');
    const devicesContainer = $('#devicesContainer');
    const selectedDeviceInput = $('#selectedDevice');
    
    // --- سلکتورهای تقوim ---
    const calendarContainerEl = document.getElementById('calendarContainer');
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
    
    let calendarInstance = null; // متغیر برای نگهداری نمونه FullCalendar

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
     * (جدید) تابع کمکی برای فرمت کردن زمان (H:M)
     */
    function formatTime(date) {
        // اطمینان از اینکه زمان به درستی در منطقه زمانی تهران نمایش داده می‌شود
        return date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Tehran' });
    }

    /**
     * (جدید) تابع کمکی برای فرمت کردن تاریخ (YYYY-MM-DD)
     */
    function getIsoDate(date) {
        // تبدیل تاریخ به رشته تاریخ محلی (ISO) بر اساس منطقه زمانی مرورگر
        let localDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000));
        return localDate.toISOString().split('T')[0];
    }
    
    /**
     * (جدید) تابع نمایش اسلات‌ها برای روزی که کلیک شده
     */
    function displaySlotsForDate(date) {
        if (!calendarInstance) return;

        // دریافت *تمام* اسلات‌هایی که تقوim از سرور گرفته
        const allEvents = calendarInstance.getEvents();
        const clickedDateStr = getIsoDate(date);

        // فیلتر کردن اسلات‌ها فقط برای روزی که کلیک شده
        const slotsForDay = allEvents
            .filter(event => getIsoDate(event.start) === clickedDateStr)
            .sort((a, b) => a.start - b.start); // مرتب‌سازی بر اساس زمان

        slotsContainer.html(''); // پاک کردن اسلات‌های قبلی
        confirmBtn.prop('disabled', true);
        selectedSlotInput.val('');

        if (slotsForDay.length > 0) {
            slotsContainer.html('<h5 class="text-muted mb-3">۴. انتخاب ساعت:</h5>');
            const slotsGrid = $('<div class="d-flex flex-wrap gap-2"></div>');
            
            slotsForDay.forEach(slot => {
                const startTimeStr = formatTime(slot.start);
                const button = $(`<button type="button" class="btn btn-outline-primary" data-slot-iso="${slot.start.toISOString()}">${startTimeStr}</button>`);
                
                button.on('click', function() {
                    slotsContainer.find('button').removeClass('active'); 
                    $(this).addClass('active');
                    
                    // --- اصلاحیه مهم ---
                    // بک‌اند (views.py) انتظار فرمت 'YYYY-MM-DD HH:MM' را دارد
                    // ما باید آن را بسازیم.
                    const isoDate = $(this).data('slot-iso');
                    const d = new Date(isoDate);
                    
                    // فرمت کردن دستی به شکلی که بک‌اند انتظار دارد
                    // (استفاده از توابع UTC برای جلوگیری از خطای Timezone)
                    const year = d.getUTCFullYear();
                    const month = (d.getUTCMonth() + 1).toString().padStart(2, '0');
                    const day = d.getUTCDate().toString().padStart(2, '0');
                    const hour = d.getUTCHours().toString().padStart(2, '0');
                    const minute = d.getUTCMinutes().toString().padStart(2, '0');
                    const backendFormat = `${year}-${month}-${day} ${hour}:${minute}`;

                    selectedSlotInput.val(backendFormat); 
                    confirmBtn.prop('disabled', false);
                });
                slotsGrid.append(button);
            });
            slotsContainer.append(slotsGrid);
        } else {
            // این حالت نباید رخ دهد، چون روز غیرقابل کلیک می‌شد
            slotsContainer.append('<div class="alert alert-warning">هیچ اسلاتی یافت نشد.</div>');
        }
    }

    /**
     * (جدید) تابع اصلی راه‌اندازی یا به‌روزرسانی تقوim
     */
    function _updateCalendar() {
        // پاک کردن اسلات‌های قبلی
        slotsContainer.html('');
        confirmBtn.prop('disabled', true);
        selectedSlotInput.val('');

        // اگر قبلاً نمونه‌ای از تقوim ساخته شده، آن را نابود کن
        if (calendarInstance) {
            calendarInstance.destroy();
            calendarInstance = null;
        }

        // بررسی اینکه آیا خدمات لازم انتخاب شده‌اند یا خیر
        let service_ids = [];
        $('.service-item:checked').each(function() {
            service_ids.push($(this).val());
        });
        const deviceId = selectedDeviceInput.val() || '';
        const hasRequiredDevice = $('#deviceSelect').length > 0;

        if (service_ids.length === 0 || (hasRequiredDevice && !deviceId)) {
            let msg = service_ids.length === 0 
                ? 'لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.' 
                : 'لطفاً دستگاه مورد نظر را انتخاب کنید.';
            $(calendarContainerEl).html(`<div class="alert alert-info">${msg}</div>`);
            return;
        }

        // --- اینجا FullCalendar ساخته می‌شود ---
        calendarInstance = new FullCalendar.Calendar(calendarContainerEl, {
            
            initialView: 'dayGridMonth', // <-- *** این خط برای حل مشکل تقویم دو-ماهه اضافه شده بود ***

            // --- ۱. تنظیمات جلالی و فارسی (اصلاح‌شده) ---
            locale: 'fa', // فعال‌سازی زبان فارسی
            calendarSystem: 'jalali', // <-- *** این خط فعال شد ***

            // --- ۲. ظاهر و هدر (اصلاح شد) ---
            headerToolbar: {
                start: 'prev',
                center: 'title',
                end: 'next'
            },
            themeSystem: 'bootstrap5',
            height: 'auto', // ارتفاع خودکار بر اساس محتوا
            
            views: {
                dayGridMonth: {
                    // titleFormat از اینجا حذف شد. calendarSystem خودش عنوان را درست می‌کند.
                    fixedWeekCount: false, // جلوگیری از نمایش ۶ هفته ثابت
                    showNonCurrentDates: false // پنهان کردن روزهای ماه قبل/بعد
                }
            },
            
            // --- ۳. منبع رویدادها (اتصال به API جدید ما) ---
            eventSources: [
                {
                    url: GET_SLOTS_URL, // API واحد و جدید
                    method: 'GET',
                    // پارامترهای اضافه‌ای که باید با هر درخواست ارسال شوند
                    extraParams: function() {
                        let service_ids = [];
                        $('.service-item:checked').each(function() {
                            service_ids.push($(this).val());
                        });
                        
                        return {
                            // ارسال آرایه service_ids به فرمتی که Django می‌فهمد
                            'service_ids[]': service_ids, 
                            'device_id': selectedDeviceInput.val() || ''
                        };
                    },
                    // --- غلط املایی اصلاح شد ---
                    failure: function() {
                        alert('خطا در بارگذاری اطلاعات تقویم از سرور.');
                    }
                }
            ],
            
            // --- ۴. مدیریت رندر و کلیک ---
            
            // نمایش loading...
            loading: function(isLoading) {
                if (isLoading) {
                    $(calendarContainerEl).prepend('<div class="fc-loading"><div class="spinner-border text-primary" role="status"></div></div>');
                } else {
                    $(calendarContainerEl).find('.fc-loading').remove();
                }
            },

            // تابع برای رنگ‌آمیزی روزهای در دسترس/غیر در دسترس
            dayCellDidMount: function(info) {
                // اگر روز در گذشته است، آن را غیرفعال کن
                const today = new Date();
                today.setHours(0, 0, 0, 0); // نادیده گرفتن ساعت
                if (info.date < today) {
                    info.el.classList.add('fc-day-past');
                    return;
                }

                // بررسی اینکه آیا اسلاتی برای این روز وجود دارد یا خیر
                // نکته: getEvents() تمام رویدادهای *بارگذاری شده* را برمی‌گرداند
                const eventsOnDay = calendarInstance.getEvents().filter(event => 
                    getIsoDate(event.start) === getIsoDate(info.date)
                );

                if (eventsOnDay.length > 0) {
                    info.el.classList.add('fc-day-available');
                } else {
                    info.el.classList.add('fc-day-unavailable');
                }
            },

            // رویداد کلیک روی یک روز
            dateClick: function(info) {
                // اگر روز در گذشته یا غیر در دسترس (خاکستری) بود، نادیده بگیر
                if (info.dayEl.classList.contains('fc-day-past') || 
                    info.dayEl.classList.contains('fc-day-unavailable')) {
                    // پاک کردن اسلات‌ها اگر روز دیگری انتخاب شده بود
                    slotsContainer.html('');
                    confirmBtn.prop('disabled', true);
                    selectedSlotInput.val('');
                    return; 
                }
                
                // در غیر این صورت (روز سبز و در دسترس است)
                // اسلات‌های آن روز را از دیتای موجود فیلتر و نمایش بده
                displaySlotsForDate(info.date);
            }
        });

        // رندر کردن تقوim
        calendarInstance.render();
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
        slotsContainer.html('');
        
        selectedSlotInput.val('');
        confirmBtn.prop('disabled', true);
        basePriceInput.val(0);
        totalDurationInput.val(0);
        codeDiscountAmount = 0;
        discountCodeInput.val('');
        discountMessage.text('').removeClass('text-success text-danger');
        updateFinalPrice();
        
        // تقوim را هم ریست کن
        if (calendarInstance) {
            calendarInstance.destroy();
            calendarInstance = null;
        }
        $(calendarContainerEl).html('<div class="alert alert-info">لطفاً ابتدا حداقل یک خدمت را انتخاب کنید.</div>');

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
        
        // --- مهم: به جای فراخوانی API، فقط تقوim را رفرش کن ---
        _updateCalendar();
    });
    
    /**
     * رویداد انتخاب دستگاه
     */
    $(document).on('change', '#deviceSelect', function() {
        selectedDeviceInput.val($(this).val());
        console.log("دستگاه عوض شد.");

        // --- مهم: به جای فراخوانی API، فقط تقوim را رفرش کن ---
        _updateCalendar();
    });

    // ====================================================================
    // --- ۳. رویدادهای تخفیف و ثبت نهایی ---
    // (این بخش‌ها کاملاً بدون تغییر هستند)
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
        // (اعتبارسنجی دستگاه بدون تغییر)
        const deviceSelect = $('#deviceSelect');
        if (deviceSelect.length > 0 && !selectedDeviceInput.val()) {
             alert('لطفا دستگاه مورد نظر را انتخاب کنید.');
             deviceSelect.focus();
             return;
        }
        
        // (اعتبارسنجی فرم بدون تغییر)
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
    // (تابع راه‌انداز تقویم در اینجا صدا زده *نمی‌شود*،
    // چون ابتدا باید خدمت انتخاب شود)
});