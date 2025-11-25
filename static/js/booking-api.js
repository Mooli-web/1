/* static/js/booking-api.js */
/**
 * لایه ارتباط با سرور (API Layer).
 * تمام درخواست‌های AJAX در این فایل مدیریت می‌شوند.
 */

const BookingAPI = {
    /**
     * دریافت لیست خدمات یک گروه خاص
     * @param {string} apiUrl - آدرس API
     * @param {number} groupId - شناسه گروه
     */
    async fetchServicesForGroup(apiUrl, groupId) {
        if (!apiUrl || !groupId) return null;

        try {
            const response = await fetch(`${apiUrl}?group_id=${groupId}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error('خطا در دریافت خدمات');
            return await response.json();
        } catch (error) {
            console.error('BookingAPI Error (Services):', error);
            return null;
        }
    },

    /**
     * دریافت لیست اسلات‌های خالی
     */
    async fetchAvailableSlots(apiUrl, serviceIds, deviceId = null) {
        if (!apiUrl || !serviceIds || serviceIds.length === 0) return null;

        const params = new URLSearchParams();
        serviceIds.forEach(id => params.append('service_ids[]', id));
        if (deviceId) params.append('device_id', deviceId);

        try {
            const response = await fetch(`${apiUrl}?${params.toString()}`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (!response.ok) throw new Error('خطا در دریافت نوبت‌ها');
            return await response.json();
        } catch (error) {
            console.error('BookingAPI Error (Slots):', error);
            return null;
        }
    },

    /**
     * اعمال کد تخفیف
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
            return { status: 'error', message: 'خطای ارتباط با سرور.' };
        }
    }
};

window.BookingAPI = BookingAPI;