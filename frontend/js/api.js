/**
 * API Service for Pakistani Gym Management System
 */

const API_BASE = window.API_BASE_URL || '/api';

const api = {
    getToken() {
        return localStorage.getItem('gym_token') || '';
    },

    setToken(token) {
        localStorage.setItem('gym_token', token);
    },

    getUser() {
        const u = localStorage.getItem('gym_user');
        return u ? JSON.parse(u) : null;
    },

    setUser(user) {
        localStorage.setItem('gym_user', JSON.stringify(user));
    },

    clearAuth() {
        localStorage.removeItem('gym_token');
        localStorage.removeItem('gym_user');
    },

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers
            });

            const data = await res.json().catch(() => ({}));

            if (!res.ok) {
                const errorMsg = data.detail || data.message || `Request failed with status ${res.status}`;
                throw new Error(errorMsg);
            }

            return data;
        } catch (err) {
            console.error(`API Error on ${endpoint}:`, err);
            throw err;
        }
    },

    // --- Auth Endpoints ---
    async login(username, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        if (data.access_token) {
            this.setToken(data.access_token);
            this.setUser(data.user);
        }
        return data;
    },

    async getMe() {
        return this.request('/auth/me');
    },

    // --- Dashboard ---
    async getDashboard() {
        return this.request('/dashboard');
    },

    // --- Members ---
    async getMembers(params = {}) {
        const qry = new URLSearchParams(params).toString();
        return this.request(`/members?${qry}`);
    },

    async quickSearch(query) {
        return this.request(`/members/quick-search?q=${encodeURIComponent(query)}`);
    },

    async getMember(id) {
        return this.request(`/members/${id}`);
    },

    async addMember(data) {
        return this.request('/members', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateMember(id, data) {
        return this.request(`/members/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async deleteMember(id) {
        return this.request(`/members/${id}`, {
            method: 'DELETE'
        });
    },

    // --- Plans ---
    async getPlans(activeOnly = false) {
        return this.request(`/plans?active_only=${activeOnly}`);
    },

    async createPlan(data) {
        return this.request('/plans', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updatePlan(id, data) {
        return this.request(`/plans/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    // --- Attendance ---
    async getTodayAttendance() {
        return this.request('/attendance/today');
    },

    async checkIn(memberId, allowDuplicate = false) {
        return this.request('/attendance/check-in', {
            method: 'POST',
            body: JSON.stringify({ member_id: memberId, allow_duplicate: allowDuplicate })
        });
    },

    async checkOut(attendanceId) {
        return this.request('/attendance/check-out', {
            method: 'POST',
            body: JSON.stringify({ attendance_id: attendanceId })
        });
    },

    async getAttendanceHistory(params = {}) {
        const qry = new URLSearchParams(params).toString();
        return this.request(`/attendance/history?${qry}`);
    },

    // --- Payments & Renewals ---
    async getPayments(params = {}) {
        const qry = new URLSearchParams(params).toString();
        return this.request(`/payments?${qry}`);
    },

    async getPaymentSummary() {
        return this.request('/payments/summary');
    },

    async recordPayment(data) {
        return this.request('/payments', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async renewMembership(data) {
        return this.request('/payments/renew', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async getReceipt(paymentId) {
        return this.request(`/payments/${paymentId}/receipt`);
    },

    // --- Expenses ---
    async getExpenses(params = {}) {
        const qry = new URLSearchParams(params).toString();
        return this.request(`/expenses?${qry}`);
    },

    async getExpenseSummary() {
        return this.request('/expenses/summary');
    },

    async addExpense(data) {
        return this.request('/expenses', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // --- Staff & Trainers ---
    async getStaff() {
        return this.request('/staff');
    },

    async addStaff(data) {
        return this.request('/staff', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateStaff(id, data) {
        return this.request(`/staff/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async deleteStaff(id) {
        return this.request(`/staff/${id}`, {
            method: 'DELETE'
        });
    },

    async getTrainers() {
        return this.request('/trainers');
    },

    async addTrainer(data) {
        return this.request('/trainers', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateTrainer(id, data) {
        return this.request(`/trainers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    // --- Reports ---
    async getFinancialReport(timeframe = 'month', start = null, end = null) {
        let url = `/reports/financial?timeframe=${timeframe}`;
        if (start && end) url += `&start_date=${start}&end_date=${end}`;
        return this.request(url);
    },

    async getMembershipReport() {
        return this.request('/reports/membership');
    },

    async getAttendanceReport() {
        return this.request('/reports/attendance');
    },

    // --- Settings ---
    async getSettings() {
        return this.request('/settings');
    },

    async updateSettings(data) {
        return this.request('/settings', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
};
