/* static/js/booking-state.js */
/**
 * مدیریت وضعیت (State Management) سیستم رزرو.
 * این شیء وظیفه نگهداری داده‌های موقت کاربر در حین پروسه رزرو را بر عهده دارد.
 */

const BookingState = {
    state: {
        selectedServices: [], // آرایه‌ای از ID خدمات انتخاب شده
        selectedDevice: null, // ID دستگاه انتخاب شده (در صورت نیاز)
        selectedDate: null,   // تاریخ انتخاب شده (شمسی)
        selectedSlot: null,   // اسلات زمانی انتخاب شده (ISO String)
    },

    /**
     * راه‌اندازی اولیه وضعیت
     */
    init() {
        this.reset();
    },

    /**
     * بازنشانی وضعیت به مقادیر پیش‌فرض
     */
    reset() {
        this.state = {
            selectedServices: [],
            selectedDevice: null,
            selectedDate: null,
            selectedSlot: null
        };
        console.log('Booking State Reset');
    },

    /**
     * به‌روزرسانی خدمات انتخاب شده
     * @param {Array} serviceIds - لیست ID خدمات
     */
    setServices(serviceIds) {
        this.state.selectedServices = serviceIds;
        // با تغییر سرویس، اسلات انتخاب شده باید پاک شود چون ممکن است دیگر معتبر نباشد
        this.state.selectedSlot = null; 
    },

    /**
     * انتخاب یا تغییر دستگاه
     * @param {number|string} deviceId 
     */
    setDevice(deviceId) {
        this.state.selectedDevice = deviceId;
        this.state.selectedSlot = null;
    },

    /**
     * انتخاب یک اسلات زمانی
     * @param {string} slotData - داده‌های اسلات (زمان شروع)
     */
    setSlot(slotData) {
        this.state.selectedSlot = slotData;
    },

    /**
     * دریافت وضعیت فعلی
     */
    get() {
        return { ...this.state }; // بازگرداندن کپی برای جلوگیری از تغییر مستقیم
    },

    /**
     * بررسی اعتبار وضعیت برای رفتن به مرحله بعد
     */
    isValid() {
        return this.state.selectedServices.length > 0 && this.state.selectedSlot !== null;
    }
};

// اتصال به آبجکت window برای دسترسی جهانی (در صورت عدم استفاده از ماژول‌های ES6)
window.BookingState = BookingState;