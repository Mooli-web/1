/* static/js/booking-api.js */
/**
 * لایه ارتباط با سرور (API Layer).
 * تمام درخواست‌های AJAX در این فایل مدیریت می‌شوند.
 */

const BookingAPI = {
    /**
     * دریافت لیست اسلات‌های خالی برای یک بازه زمانی.
     * * @param {string} apiUrl - آدرس API (توسط جنگو تولید می‌شود)
     * @param {Array} serviceIds - لیست خدمات
     * @param {string|null} deviceId - دستگاه (اختیاری)
     * @returns {Promise} - خروجی JSON سرور
     */
    async fetchAvailableSlots(apiUrl, serviceIds, deviceId = null) {
        if (!apiUrl) {
            console.error('BookingAPI: API URL is missing.');
            return null;
        }

        // ساخت پارامترهای URL
        const params = new URLSearchParams();
        serviceIds.forEach(id => params.append('service_ids[]', id));
        if (deviceId) {
            params.append('device_id', deviceId);
        }

        try {
            const response = await fetch(`${apiUrl}?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('BookingAPI Error:', error);
            // نمایش پیام خطا به کاربر (اختیاری)
            // alert('خطا در دریافت نوبت‌های خالی. لطفا اتصال اینترنت خود را بررسی کنید.');
            return null;
        }
    },

    /**
     * اعمال کد تخفیف
     * @param {string} apiUrl 
     * @param {string} code 
     * @param {number} totalPrice 
     * @param {string} csrfToken 
     */
    async applyDiscount(apiUrl, code, totalPrice, csrfToken) {
        const formData = new FormData();
        formData.append('code', code);
        formData.append('total_price', totalPrice);

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            });
            return await response.json();
        } catch (error) {
            console.error('Discount API Error:', error);
            return { status: 'error', message: 'خطای سیستمی.' };
        }
    }
};

window.BookingAPI = BookingAPI;