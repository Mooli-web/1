// static/js/booking-state.js
// وظیفه: ایجاد Namespace سراسری BookingApp و تعریف تمام متغیرهای State و سلکتورهای UI.
// این فایل باید اولین فایل اسکریپت در create_booking.html باشد.

window.BookingApp = {
    // 1. State: متغیرهای مربوط به وضعیت برنامه
    state: {
        // از data- attributes خوانده می‌شوند
        GET_SLOTS_URL: null,
        GET_SERVICES_URL: null,
        APPLY_DISCOUNT_URL: null,
        CSRF_TOKEN: null,
        MAX_DISCOUNT: 0,
        TODAY_DATE_SERVER: null,

        // متغیرهای داخلی
        codeDiscountAmount: 0,
        allGroupedSlots: {},
        todayJalali: null,
        currentCalendarMoment: null,
        
        // تایمر FOMO
        fomoExpirationTimer: null,
        fomoIntervalTimer: null,
        FOMO_DURATION_SECONDS: 5 * 60 // 5 دقیقه
    },

    // 2. UI: تمام سلکتورهای jQuery (برای دسترسی آسان)
    ui: {
        bookingForm: null,
        serviceGroupSelect: null,
        servicesContainer: null,
        devicesContainer: null,
        selectedDeviceInput: null,
        slotsContainer: null,
        calendarStepLabel: null,
        calendarWrapper: null,
        calendarGridBody: null,
        calendarMonthLabel: null,
        prevMonthBtn: null,
        nextMonthBtn: null,
        timeSelectionContainer: null,
        slotsLoader: null,
        slotsInitialMessage: null,
        firstAvailableContainer: null,
        firstSlotLabel: null,
        bookFirstSlotBtn: null,
        fomoTimerMessage: null,
        selectedSlotInput: null,
        confirmBtn: null,
        submitBtn: null,
        applyPointsCheckbox: null,
        finalPriceSpan: null,
        confirmationModal: null,
        infoConfirmationCheck: null,
        discountCodeInput: null,
        applyDiscountBtn: null,
        discountMessage: null,
        basePriceInput: null,
        totalDurationInput: null
    },

    // 3. Namespaces برای توابع (توسط فایل‌های دیگر پر می‌شوند)
    api: {},
    uiHelpers: {},
    init: {}
};