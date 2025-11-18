// static/js/booking-state.js
// وظیفه: ایجاد Namespace سراسری BookingApp و تعریف تمام متغیرهای State.

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
        PRICE_TO_POINTS_RATE: 0, // <-- متغیر جدید: نرخ تبدیل

        // متغیرهای داخلی
        codeDiscountAmount: 0,
        allGroupedSlots: {},
        todayMoment: null,
        currentCalendarMoment: null,
        
        // تایمر FOMO
        fomoExpirationTimer: null,
        fomoIntervalTimer: null,
        FOMO_DURATION_SECONDS: 5 * 60
    },

    // 2. UI: تمام سلکتورهای jQuery
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
        totalDurationInput: null,
        rewardBox: null, // <-- المنت جدید
        rewardText: null  // <-- متن داخل المنت
    },

    // 3. Namespaces
    api: {},
    uiHelpers: {},
    init: {}
};