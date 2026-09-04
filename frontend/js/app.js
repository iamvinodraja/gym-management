/**
 * Main Application Logic for Pakistani Gym Management System
 */

const app = {
    state: {
        currentUser: null,
        currentView: 'dashboard',
        settings: {},
        plans: [],
        trainers: [],
        members: []
    },

    async init() {
        this.setupNavigation();
        this.setupGlobalSearch();
        this.setupModals();

        // Load Gym settings
        try {
            this.state.settings = await api.getSettings();
            this.updateBrandingUI();
        } catch (e) {
            console.warn('Could not load settings:', e);
        }

        // Enforce Login Check: Only authenticated users can access the system
        const token = api.getToken();
        const user = api.getUser();

        if (!token || !user) {
            this.showLoginScreen();
            return;
        }

        // Verify session with backend
        try {
            const me = await api.getMe();
            this.state.currentUser = me;
            this.updateUserUI();
            this.hideLoginScreen();

            // Load initial data
            await this.loadPlans();
            await this.loadTrainers();

            // Navigate to initial view
            this.navigateTo('dashboard');
        } catch (err) {
            console.warn('Session expired or unauthorized. Showing login page:', err);
            api.clearAuth();
            this.showLoginScreen();
        }
    },

    showLoginScreen() {
        const screen = document.getElementById('loginScreen');
        if (screen) screen.classList.remove('hidden');
    },

    hideLoginScreen() {
        const screen = document.getElementById('loginScreen');
        if (screen) screen.classList.add('hidden');
    },

    async handleLogin(e) {
        e.preventDefault();
        const uInput = document.getElementById('loginUsername');
        const pInput = document.getElementById('loginPassword');
        const errAlert = document.getElementById('loginErrorAlert');
        const errText = document.getElementById('loginErrorText');
        const btn = document.getElementById('loginSubmitBtn');

        if (!uInput || !pInput) return;
        const username = uInput.value.trim();
        const password = pInput.value;

        if (errAlert) errAlert.style.display = 'none';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
        }

        try {
            const res = await api.login(username, password);
            this.state.currentUser = res.user;
            this.updateUserUI();
            this.hideLoginScreen();
            this.showToast(`Signed in successfully as ${res.user.full_name}`, 'success');

            // Load initial data and open dashboard
            await this.loadPlans();
            await this.loadTrainers();
            this.navigateTo('dashboard');
        } catch (err) {
            if (errAlert && errText) {
                errText.textContent = err.message || 'Invalid username or password. Access denied.';
                errAlert.style.display = 'flex';
            } else {
                this.showToast(err.message || 'Login failed', 'error');
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In to Portal';
            }
        }
    },

    logout() {
        api.clearAuth();
        this.state.currentUser = null;
        this.showLoginScreen();
        this.showToast('You have been logged out.', 'success');
    },

    updateBrandingUI() {
        const s = this.state.settings;
        if (s.gym_name) {
            document.querySelectorAll('.gym-brand-name').forEach(el => el.textContent = s.gym_name);
        }
        if (s.gym_address) {
            document.querySelectorAll('.gym-brand-address').forEach(el => el.textContent = s.gym_address);
        }
    },

    updateUserUI() {
        const u = this.state.currentUser;
        const nameEl = document.getElementById('headerUserName');
        const roleEl = document.getElementById('headerUserRole');
        const avatarEl = document.getElementById('headerUserAvatar');

        if (u) {
            if (nameEl) nameEl.textContent = u.full_name || u.username;
            if (roleEl) {
                roleEl.textContent = u.role.toUpperCase();
                roleEl.className = `user-role-badge role-${u.role.toLowerCase()}`;
            }
            if (avatarEl) avatarEl.textContent = (u.full_name || u.username).charAt(0).toUpperCase();
        }
    },

    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = link.getAttribute('data-view');
                if (view) this.navigateTo(view);
            });
        });

        // Mobile sidebar toggle
        const toggleBtn = document.getElementById('sidebarToggleBtn');
        const sidebar = document.querySelector('.sidebar');
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }
    },

    navigateTo(viewName) {
        this.state.currentView = viewName;

        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.getAttribute('data-view') === viewName);
        });

        // Switch active section
        document.querySelectorAll('.view-section').forEach(sec => {
            sec.classList.remove('active');
        });
        const target = document.getElementById(`${viewName}View`);
        if (target) {
            target.classList.add('active');
        }

        // Close mobile sidebar if open
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) sidebar.classList.remove('open');

        // Trigger view loader
        switch (viewName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'members':
                this.loadMembers();
                break;
            case 'attendance':
                this.loadAttendanceView();
                break;
            case 'memberships':
                this.loadPlans();
                break;
            case 'payments':
                this.loadPaymentsView();
                break;
            case 'expenses':
                this.loadExpensesView();
                break;
            case 'trainers':
                this.loadTrainersAndStaff();
                break;
            case 'reports':
                this.loadReportsView();
                break;
            case 'settings':
                this.loadSettingsView();
                break;
        }
    },

    // --- Toast Notifications ---
    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;

        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    },

    // --- Global Search Bar ---
    setupGlobalSearch() {
        const searchInput = document.getElementById('globalSearchInput');
        const dropdown = document.getElementById('searchResultsDropdown');
        if (!searchInput || !dropdown) return;

        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const val = e.target.value.trim();
            if (val.length < 1) {
                dropdown.style.display = 'none';
                return;
            }

            debounceTimer = setTimeout(async () => {
                try {
                    const results = await api.quickSearch(val);
                    if (results.length === 0) {
                        dropdown.innerHTML = `<div style="padding: 14px; text-align: center; color: var(--text-dim); font-size: 12px;">No members found matching "${val}"</div>`;
                    } else {
                        dropdown.innerHTML = results.map(m => `
                            <div class="search-result-item" onclick="app.selectSearchResult(${m.id})">
                                <div class="search-res-info">
                                    <h4>${m.full_name} <span class="member-code-badge" style="font-size: 11px;">${m.member_id}</span></h4>
                                    <p>${m.phone} • Plan: ${m.plan_name} • Expiry: ${m.expiry_date || 'N/A'}</p>
                                </div>
                                <div style="display: flex; gap: 6px; align-items: center;" onclick="event.stopPropagation()">
                                    <button class="btn btn-secondary btn-sm" onclick="app.viewMemberProfile(${m.id})">Profile</button>
                                    <button class="btn btn-cyan btn-sm" onclick="app.quickCheckIn(${m.id})">
                                        <i class="fas fa-sign-in-alt"></i> Check In
                                    </button>
                                    <button class="btn btn-amber btn-sm" onclick="app.openPaymentModal(${m.id})">Pay</button>
                                </div>
                            </div>
                        `).join('');
                    }
                    dropdown.style.display = 'block';
                } catch (err) {
                    console.error('Search error:', err);
                }
            }, 250);
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    },

    selectSearchResult(memberId) {
        const dropdown = document.getElementById('searchResultsDropdown');
        if (dropdown) dropdown.style.display = 'none';
        this.viewMemberProfile(memberId);
    },

    // --- Modal Management ---
    setupModals() {
        document.querySelectorAll('.modal-close-btn, .modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const overlay = e.target.closest('.modal-overlay');
                if (overlay) overlay.classList.remove('active');
            });
        });

        // Close modal when clicking backdrop
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    overlay.classList.remove('active');
                }
            });
        });
    },

    openModal(modalId) {
        const m = document.getElementById(modalId);
        if (m) m.classList.add('active');
    },

    closeModal(modalId) {
        const m = document.getElementById(modalId);
        if (m) m.classList.remove('active');
    },

    // --- Dashboard View ---
    async loadDashboard() {
        try {
            const data = await api.getDashboard();
            if (!data) return;
            const k = data.kpis || {};

            const setElText = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = (val !== undefined && val !== null) ? val : '';
            };

            // Populate KPIs safely
            setElText('kpiTotalMembers', k.total_members ?? 0);
            setElText('kpiActiveMembers', k.active_members ?? 0);
            setElText('kpiExpiredMembers', k.expired_members ?? 0);
            setElText('kpiExpiringSoon', k.expiring_soon ?? 0);
            setElText('kpiTodayAttendance', k.today_attendance ?? 0);
            setElText('kpiTodayCollections', k.today_collections_formatted || 'Rs. 0');
            setElText('kpiMonthCollections', k.month_collections_formatted || 'Rs. 0');
            setElText('kpiPendingPayments', k.pending_payments_formatted || 'Rs. 0');
            setElText('kpiNewThisMonth', k.new_members_this_month ?? 0);

            // Today's Attendance Table
            try {
                const attBody = document.getElementById('dashboardAttendanceBody');
                if (attBody) {
                    const todayAtt = data.today_attendance || [];
                    if (todayAtt.length === 0) {
                        attBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 20px;">No attendance check-ins recorded today yet.</td></tr>`;
                    } else {
                        attBody.innerHTML = todayAtt.map(a => views.renderTodayAttendanceRow(a)).join('');
                    }
                }
            } catch (attErr) {
                console.warn('Error rendering today attendance:', attErr);
            }

            // Expiring Soon Table
            try {
                const expBody = document.getElementById('dashboardExpiringBody');
                if (expBody) {
                    const expiring = data.expiring_soon || [];
                    if (expiring.length === 0) {
                        expBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 20px;">No memberships expiring within the next 7 days.</td></tr>`;
                    } else {
                        expBody.innerHTML = expiring.map(m => views.renderExpiringRow(m)).join('');
                    }
                }
            } catch (expErr) {
                console.warn('Error rendering expiring soon:', expErr);
            }

            // Recent Payments Table
            try {
                const payBody = document.getElementById('dashboardPaymentsBody');
                if (payBody) {
                    const recentPays = data.recent_payments || [];
                    if (recentPays.length === 0) {
                        payBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 20px;">No recent payments recorded.</td></tr>`;
                    } else {
                        payBody.innerHTML = recentPays.map(p => views.renderPaymentRow(p)).join('');
                    }
                }
            } catch (payErr) {
                console.warn('Error rendering recent payments:', payErr);
            }

            // Recent Activity Feed
            try {
                const actList = document.getElementById('dashboardActivityList');
                if (actList) {
                    const activities = data.recent_activities || [];
                    if (activities.length === 0) {
                        actList.innerHTML = `<li style="color: var(--text-dim); font-size: 13px;">No recent activities logged.</li>`;
                    } else {
                        actList.innerHTML = activities.map(act => {
                            const action = act?.action || 'Activity';
                            const desc = act?.description || '';
                            const time = act?.time || '';
                            const performedBy = act?.performed_by || 'System';
                            const icon = this.getActivityIcon(action);
                            return `
                                <li class="activity-item">
                                    <div class="activity-icon-bubble">
                                        <i class="fas ${icon}"></i>
                                    </div>
                                    <div>
                                        <div class="activity-desc">${desc}</div>
                                        <div class="activity-meta">${time} • by ${performedBy}</div>
                                    </div>
                                </li>
                            `;
                        }).join('');
                    }
                }
            } catch (actErr) {
                console.warn('Error rendering recent activities:', actErr);
            }

        } catch (err) {
            console.error('Failed to load dashboard:', err);
            this.showToast('Error loading dashboard data: ' + (err.message || 'Please retry'), 'error');
        }
    },

    getActivityIcon(action) {
        if (!action || typeof action !== 'string') return 'fa-bell';
        if (action.includes('Registered')) return 'fa-user-plus';
        if (action.includes('Fee') || action.includes('Payment')) return 'fa-receipt';
        if (action.includes('Renewed')) return 'fa-sync-alt';
        if (action.includes('Check-In') || action.includes('Checked In')) return 'fa-sign-in-alt';
        if (action.includes('Check-Out') || action.includes('Checked Out')) return 'fa-sign-out-alt';
        return 'fa-bell';
    },

    // --- Members View ---
    async loadMembers() {
        const q = document.getElementById('memberSearchInput')?.value || '';
        const status = document.getElementById('memberStatusFilter')?.value || 'all';
        const planId = document.getElementById('memberPlanFilter')?.value || '';
        const duesOnly = document.getElementById('memberDuesFilter')?.checked || false;

        const params = {};
        if (q) params.q = q;
        if (status !== 'all') params.status = status;
        if (planId) params.plan_id = planId;
        if (duesOnly) params.has_dues = 'true';

        try {
            const members = await api.getMembers(params);
            this.state.members = members;

            const tbody = document.getElementById('membersTableBody');
            if (!tbody) return;

            if (members.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 30px;">No members found matching the filters.</td></tr>`;
            } else {
                tbody.innerHTML = members.map(m => views.renderMemberRow(m)).join('');
            }
        } catch (err) {
            console.error('Failed to load members:', err);
            this.showToast('Error loading member list', 'error');
        }
    },

    // --- Add Member Flow ---
    openAddMemberModal() {
        const form = document.getElementById('addMemberForm');
        if (form) form.reset();

        // Populate plans dropdown
        const planSelect = document.getElementById('newMemberPlan');
        if (planSelect) {
            planSelect.innerHTML = '<option value="">-- Select Plan --</option>' + 
                this.state.plans.filter(p => p.is_active).map(p => `
                    <option value="${p.id}" data-price="${p.price}" data-days="${p.duration_days}">
                        ${p.name} - ${p.price_formatted} (${p.duration_days} days)
                    </option>
                `).join('');
        }

        // Populate trainers dropdown
        const trainerSelect = document.getElementById('newMemberTrainer');
        if (trainerSelect) {
            trainerSelect.innerHTML = '<option value="">-- No Trainer Assigned --</option>' + 
                this.state.trainers.map(t => `<option value="${t.id}">${t.name} (${t.specialization})</option>`).join('');
        }

        // Set default dates
        const todayIso = new Date().toISOString().split('T')[0];
        const joinInput = document.getElementById('newMemberJoinDate');
        const startInput = document.getElementById('newMemberStartDate');
        if (joinInput) joinInput.value = todayIso;
        if (startInput) startInput.value = todayIso;

        this.openModal('addMemberModal');
    },

    onAddMemberPlanChange() {
        const select = document.getElementById('newMemberPlan');
        const feeInput = document.getElementById('newMemberFee');
        const amountPaidInput = document.getElementById('newMemberPaid');
        if (!select || !feeInput) return;

        const opt = select.options[select.selectedIndex];
        if (opt && opt.dataset.price) {
            const price = parseFloat(opt.dataset.price) || 0;
            feeInput.value = price;
            if (amountPaidInput && (!amountPaidInput.value || amountPaidInput.value === '0')) {
                amountPaidInput.value = price; // default to full payment
            }
        }
    },

    async submitAddMember(e) {
        e.preventDefault();
        const full_name = document.getElementById('newMemberName').value.trim();
        const phone = document.getElementById('newMemberPhone').value.trim();
        if (!full_name || !phone) {
            this.showToast('Please enter member name and phone number', 'error');
            return;
        }

        const data = {
            full_name,
            father_name: document.getElementById('newMemberFather').value.trim() || null,
            cnic: document.getElementById('newMemberCnic').value.trim() || null,
            phone,
            emergency_contact: document.getElementById('newMemberEmergency').value.trim() || null,
            gender: document.getElementById('newMemberGender').value,
            address: document.getElementById('newMemberAddress').value.trim() || null,
            join_date: document.getElementById('newMemberJoinDate').value || null,
            start_date: document.getElementById('newMemberStartDate').value || null,
            current_plan_id: parseInt(document.getElementById('newMemberPlan').value) || null,
            monthly_fee: parseFloat(document.getElementById('newMemberFee').value) || 0.0,
            discount: parseFloat(document.getElementById('newMemberDiscount').value) || 0.0,
            amount_paid: parseFloat(document.getElementById('newMemberPaid').value) || 0.0,
            payment_method: document.getElementById('newMemberPayMethod').value,
            trainer_id: parseInt(document.getElementById('newMemberTrainer').value) || null,
            notes: document.getElementById('newMemberNotes').value.trim() || null
        };

        try {
            const res = await api.addMember(data);
            this.closeModal('addMemberModal');
            this.showToast(res.message, 'success');
            await this.loadMembers();

            // If initial payment was made, prompt or show receipt
            if (res.receipt_id) {
                this.showReceipt(res.receipt_id);
            }
        } catch (err) {
            this.showToast(err.message || 'Failed to add member', 'error');
        }
    },

    // --- Member Profile View Modal ---
    async viewMemberProfile(memberId) {
        try {
            const m = await api.getMember(memberId);
            const modal = document.getElementById('memberProfileModal');
            if (!modal) return;

            // Populate Overview Header
            document.getElementById('profName').textContent = m.full_name;
            document.getElementById('profMemberId').textContent = m.member_id;
            document.getElementById('profPhone').textContent = m.phone;
            document.getElementById('profPhoneLink').href = `tel:${m.phone}`;
            document.getElementById('profStatus').textContent = m.status;
            document.getElementById('profStatus').className = `badge badge-${m.status === 'Active' ? 'active' : (m.status === 'Expiring Soon' ? 'expiring' : 'expired')}`;

            // Store current viewing member ID on modal for action buttons
            modal.dataset.memberId = m.id;

            // Tab 1: Personal Info
            document.getElementById('profFatherName').textContent = m.father_name || '-';
            document.getElementById('profCnic').textContent = m.cnic || '-';
            document.getElementById('profEmergency').textContent = m.emergency_contact || '-';
            document.getElementById('profGender').textContent = m.gender || 'Male';
            document.getElementById('profAddress').textContent = m.address || '-';
            document.getElementById('profJoinDate').textContent = m.join_date;
            document.getElementById('profTrainer').textContent = m.trainer_name || 'None';
            document.getElementById('profNotes').textContent = m.notes || 'None';

            // Tab 2: Membership & Balance
            document.getElementById('profPlanName').textContent = m.plan_name;
            document.getElementById('profStartDate').textContent = m.start_date || '-';
            document.getElementById('profExpiryDate').textContent = m.expiry_date || '-';
            document.getElementById('profRemainingDays').textContent = `${m.remaining_days} days`;
            document.getElementById('profPlanFee').textContent = m.monthly_fee_formatted;
            document.getElementById('profOutstanding').textContent = m.outstanding_formatted;

            // WhatsApp link in profile
            const cleanPhone = (m.phone || '').replace(/[^0-9]/g, '');
            const waNumber = cleanPhone.startsWith('0') ? '92' + cleanPhone.substring(1) : cleanPhone;
            const waBtn = document.getElementById('profWhatsAppBtn');
            if (waBtn) {
                if (waNumber) {
                    waBtn.style.display = 'inline-flex';
                    const msg = encodeURIComponent(`Assalam-o-Alaikum ${m.full_name}, reminder regarding your membership at Power Fitness Gym. Expiry: ${m.expiry_date}. Dues: ${m.outstanding_formatted}.`);
                    waBtn.href = `https://wa.me/${waNumber}?text=${msg}`;
                } else {
                    waBtn.style.display = 'none';
                }
            }

            // Tab 3: Payments History
            const payTbody = document.getElementById('profPaymentsBody');
            if (payTbody) {
                if (m.payments.length === 0) {
                    payTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 16px;">No payment records found.</td></tr>`;
                } else {
                    payTbody.innerHTML = m.payments.map(p => `
                        <tr>
                            <td><span class="member-code-badge">${p.payment_id}</span></td>
                            <td style="font-weight: 700; color: var(--primary);">${p.amount_formatted}</td>
                            <td><span class="badge badge-active">${p.payment_method}</span></td>
                            <td>${p.payment_date}</td>
                            <td>${p.description || '-'}</td>
                            <td>
                                <button class="btn btn-secondary btn-sm" onclick="app.showReceipt(${p.id})">
                                    <i class="fas fa-receipt"></i> Slip
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
            }

            // Tab 4: Attendance History
            const attTbody = document.getElementById('profAttendanceBody');
            if (attTbody) {
                if (m.attendances.length === 0) {
                    attTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-dim); padding: 16px;">No attendance check-ins recorded.</td></tr>`;
                } else {
                    attTbody.innerHTML = m.attendances.map(a => `
                        <tr>
                            <td>${a.date}</td>
                            <td style="color: var(--primary); font-weight: 700;">${a.check_in_time}</td>
                            <td>${a.check_out_time || '-'}</td>
                            <td><span class="badge badge-active">${a.status}</span></td>
                        </tr>
                    `).join('');
                }
            }

            // Tab 5: Membership Renewal History
            const memHistBody = document.getElementById('profMembershipsBody');
            if (memHistBody) {
                if (m.memberships.length === 0) {
                    memHistBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 16px;">No previous renewal history.</td></tr>`;
                } else {
                    memHistBody.innerHTML = m.memberships.map(mh => `
                        <tr>
                            <td style="font-weight: 600; color: #fff;">${mh.plan_name}</td>
                            <td>${mh.start_date} to ${mh.end_date}</td>
                            <td style="font-weight: 700;">${mh.fee_formatted}</td>
                            <td>Rs. ${mh.amount_paid.toLocaleString()}</td>
                            <td style="color: ${mh.remaining_balance > 0 ? 'var(--accent-rose)' : 'var(--primary)'}; font-weight: 600;">
                                Rs. ${mh.remaining_balance.toLocaleString()}
                            </td>
                        </tr>
                    `).join('');
                }
            }

            // Reset tab to Overview
            this.switchProfileTab('overview');
            this.openModal('memberProfileModal');

        } catch (err) {
            console.error('Failed to load profile:', err);
            this.showToast('Could not load member profile', 'error');
        }
    },

    switchProfileTab(tabName) {
        document.querySelectorAll('.profile-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
        });
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `tab-${tabName}`);
        });
    },

    // --- Renewal Flow ---
    async openRenewModal(memberId) {
        try {
            const m = await api.getMember(memberId);
            const modal = document.getElementById('renewMembershipModal');
            if (!modal) return;

            document.getElementById('renewMemberIdVal').value = m.id;
            document.getElementById('renewMemberNameDisplay').textContent = `${m.full_name} (${m.member_id})`;
            document.getElementById('renewCurrentExpiryDisplay').textContent = m.expiry_date || 'None';

            // Populate Plans dropdown
            const planSelect = document.getElementById('renewPlanSelect');
            planSelect.innerHTML = this.state.plans.filter(p => p.is_active).map(p => `
                <option value="${p.id}" data-price="${p.price}" data-days="${p.duration_days}" ${m.current_plan_id === p.id ? 'selected' : ''}>
                    ${p.name} - ${p.price_formatted} (${p.duration_days} days)
                </option>
            `).join('');

            this.onRenewPlanChange();
            this.openModal('renewMembershipModal');
        } catch (err) {
            this.showToast('Failed to prepare renewal modal', 'error');
        }
    },

    onRenewPlanChange() {
        const select = document.getElementById('renewPlanSelect');
        const feeInput = document.getElementById('renewFeeInput');
        const paidInput = document.getElementById('renewPaidInput');
        if (!select || !feeInput) return;

        const opt = select.options[select.selectedIndex];
        if (opt && opt.dataset.price) {
            const price = parseFloat(opt.dataset.price) || 0;
            feeInput.value = price;
            if (paidInput) paidInput.value = price; // default to paying full
            this.calculateRenewBalance();
        }
    },

    calculateRenewBalance() {
        const fee = parseFloat(document.getElementById('renewFeeInput')?.value) || 0;
        const discount = parseFloat(document.getElementById('renewDiscountInput')?.value) || 0;
        const paid = parseFloat(document.getElementById('renewPaidInput')?.value) || 0;
        const netPayable = Math.max(0, fee - discount);
        const remaining = Math.max(0, netPayable - paid);

        const balDisplay = document.getElementById('renewRemainingBalanceDisplay');
        if (balDisplay) {
            balDisplay.textContent = `Rs. ${remaining.toLocaleString()}`;
            balDisplay.style.color = remaining > 0 ? 'var(--accent-rose)' : 'var(--primary)';
        }
    },

    async submitRenewal(e) {
        e.preventDefault();
        const member_id = parseInt(document.getElementById('renewMemberIdVal').value);
        const plan_id = parseInt(document.getElementById('renewPlanSelect').value);
        const fee = parseFloat(document.getElementById('renewFeeInput').value) || 0;
        const discount = parseFloat(document.getElementById('renewDiscountInput').value) || 0;
        const amount_paid = parseFloat(document.getElementById('renewPaidInput').value) || 0;
        const payment_method = document.getElementById('renewPayMethod').value;
        const start_from_expiry = document.getElementById('renewFromExpiry').checked;

        try {
            const res = await api.renewMembership({
                member_id,
                plan_id,
                fee,
                discount,
                amount_paid,
                payment_method,
                start_from_expiry
            });

            this.closeModal('renewMembershipModal');
            this.showToast(res.message, 'success');

            // Refresh current view
            if (this.state.currentView === 'dashboard') await this.loadDashboard();
            else if (this.state.currentView === 'members') await this.loadMembers();

            if (res.receipt_id) {
                this.showReceipt(res.receipt_id);
            }
        } catch (err) {
            this.showToast(err.message || 'Renewal failed', 'error');
        }
    },

    // --- Payment Flow ---
    async openPaymentModal(memberId = null) {
        const form = document.getElementById('recordPaymentForm');
        if (form) form.reset();

        // Populate Members select
        const memberSelect = document.getElementById('paymentMemberSelect');
        if (memberSelect) {
            memberSelect.innerHTML = '<option value="">-- Choose Member --</option>' + 
                this.state.members.map(m => `
                    <option value="${m.id}" data-dues="${m.outstanding_amount}" ${memberId === m.id ? 'selected' : ''}>
                        ${m.full_name} (${m.member_id}) - Due: ${m.outstanding_formatted}
                    </option>
                `).join('');
        }

        // Set date to today
        const dateInput = document.getElementById('paymentDateInput');
        if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];

        this.onPaymentMemberChange();
        this.openModal('recordPaymentModal');
    },

    onPaymentMemberChange() {
        const select = document.getElementById('paymentMemberSelect');
        const duesDisplay = document.getElementById('paymentMemberDuesDisplay');
        const amountInput = document.getElementById('paymentAmountInput');
        if (!select || !duesDisplay) return;

        const opt = select.options[select.selectedIndex];
        if (opt && opt.dataset.dues !== undefined) {
            const dues = parseFloat(opt.dataset.dues) || 0;
            duesDisplay.textContent = `Rs. ${dues.toLocaleString()}`;
            duesDisplay.style.color = dues > 0 ? 'var(--accent-rose)' : 'var(--primary)';
            if (amountInput && dues > 0 && (!amountInput.value || amountInput.value === '0')) {
                amountInput.value = dues;
            }
        } else {
            duesDisplay.textContent = 'Rs. 0';
        }
    },

    async submitRecordPayment(e) {
        e.preventDefault();
        const member_id = parseInt(document.getElementById('paymentMemberSelect').value);
        const amount = parseFloat(document.getElementById('paymentAmountInput').value) || 0;
        const discount = parseFloat(document.getElementById('paymentDiscountInput').value) || 0;
        const payment_method = document.getElementById('paymentMethodSelect').value;
        const description = document.getElementById('paymentDescInput').value.trim();
        const payment_date = document.getElementById('paymentDateInput').value;

        if (!member_id || amount <= 0) {
            this.showToast('Please select member and specify valid amount', 'error');
            return;
        }

        try {
            const res = await api.recordPayment({
                member_id,
                amount,
                discount,
                payment_method,
                description,
                payment_date: payment_date || null
            });

            this.closeModal('recordPaymentModal');
            this.showToast(res.message, 'success');

            if (this.state.currentView === 'dashboard') await this.loadDashboard();
            else if (this.state.currentView === 'members') await this.loadMembers();
            else if (this.state.currentView === 'payments') await this.loadPaymentsView();

            if (res.payment_id) {
                this.showReceipt(res.payment_id);
            }
        } catch (err) {
            this.showToast(err.message || 'Payment recording failed', 'error');
        }
    },

    // --- Receipt Slip Modal ---
    async showReceipt(paymentId) {
        try {
            const data = await api.getReceipt(paymentId);
            const container = document.getElementById('receiptContentContainer');
            if (container) {
                container.innerHTML = views.renderReceiptHTML(data);
            }
            this.openModal('receiptModal');
        } catch (err) {
            this.showToast('Failed to load receipt slip', 'error');
        }
    },

    printCurrentReceipt() {
        window.print();
    },

    async quickCheckIn(memberId) {
        const dropdown = document.getElementById('searchResultsDropdown');
        if (dropdown) dropdown.style.display = 'none';
        try {
            const res = await api.checkIn(memberId, false);
            if (res.duplicate) {
                // Confirmation prompt for duplicate check-in
                if (confirm(`${res.message}\nDo you still want to check in again?`)) {
                    const overrideRes = await api.checkIn(memberId, true);
                    this.showToast(overrideRes.message, 'success');
                }
            } else {
                this.showToast(res.message, 'success');
            }

            if (this.state.currentView === 'dashboard') await this.loadDashboard();
            else if (this.state.currentView === 'attendance') await this.loadAttendanceView();
        } catch (err) {
            this.showToast(err.message || 'Check-in failed', 'error');
        }
    },

    async checkOutAttendance(attendanceId) {
        try {
            const res = await api.checkOut(attendanceId);
            this.showToast(res.message, 'success');
            if (this.state.currentView === 'dashboard') await this.loadDashboard();
            else if (this.state.currentView === 'attendance') await this.loadAttendanceView();
        } catch (err) {
            this.showToast('Failed to check out', 'error');
        }
    },

    async loadAttendanceView() {
        try {
            const records = await api.getTodayAttendance();
            const tbody = document.getElementById('attendanceTodayTableBody');
            if (tbody) {
                if (records.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 24px;">No members checked in today yet.</td></tr>`;
                } else {
                    tbody.innerHTML = records.map(r => views.renderTodayAttendanceRow(r)).join('');
                }
            }

            // Populate Check-in Quick Member Select
            const memberSelect = document.getElementById('quickCheckInMemberSelect');
            if (memberSelect) {
                memberSelect.innerHTML = '<option value="">-- Choose Member to Check In --</option>' + 
                    this.state.members.map(m => `<option value="${m.id}">${m.full_name} (${m.member_id}) - ${m.status}</option>`).join('');
            }
        } catch (err) {
            console.error('Attendance view error:', err);
        }
    },

    async submitQuickCheckInFromSelect() {
        const select = document.getElementById('quickCheckInMemberSelect');
        const id = parseInt(select?.value);
        if (!id) {
            this.showToast('Please select a member first', 'error');
            return;
        }
        await this.quickCheckIn(id);
        if (select) select.value = '';
    },

    // --- Plans & Memberships View ---
    async loadPlans() {
        try {
            const plans = await api.getPlans(false);
            this.state.plans = plans;

            const container = document.getElementById('plansGridContainer');
            if (container) {
                container.innerHTML = plans.map(p => views.renderPlanCard(p)).join('');
            }
        } catch (err) {
            console.error('Error loading plans:', err);
        }
    },

    async loadTrainers() {
        try {
            this.state.trainers = await api.getTrainers();
        } catch (err) {
            console.error('Error loading trainers:', err);
        }
    },

    openAddPlanModal() {
        document.getElementById('planForm').reset();
        document.getElementById('planEditId').value = '';
        document.getElementById('planModalTitle').textContent = 'Create Membership Plan';
        this.openModal('planModal');
    },

    openEditPlanModal(id, name, days, price, desc, isActive) {
        document.getElementById('planEditId').value = id;
        document.getElementById('planNameInput').value = name;
        document.getElementById('planDurationInput').value = days;
        document.getElementById('planPriceInput').value = price;
        document.getElementById('planDescInput').value = desc;
        document.getElementById('planActiveCheck').checked = isActive;
        document.getElementById('planModalTitle').textContent = 'Edit Membership Plan';
        this.openModal('planModal');
    },

    async submitPlanForm(e) {
        e.preventDefault();
        const id = document.getElementById('planEditId').value;
        const data = {
            name: document.getElementById('planNameInput').value.trim(),
            duration_days: parseInt(document.getElementById('planDurationInput').value) || 30,
            price: parseFloat(document.getElementById('planPriceInput').value) || 0.0,
            description: document.getElementById('planDescInput').value.trim() || null,
            is_active: document.getElementById('planActiveCheck').checked
        };

        try {
            if (id) {
                await api.updatePlan(id, data);
                this.showToast('Plan updated successfully', 'success');
            } else {
                await api.createPlan(data);
                this.showToast('Plan created successfully', 'success');
            }
            this.closeModal('planModal');
            await this.loadPlans();
        } catch (err) {
            this.showToast(err.message || 'Plan operation failed', 'error');
        }
    },

    async togglePlanActive(id, newStatus) {
        try {
            await api.updatePlan(id, { is_active: newStatus });
            this.showToast('Plan status updated', 'success');
            await this.loadPlans();
        } catch (err) {
            this.showToast('Failed to update plan status', 'error');
        }
    },

    // --- Payments View ---
    async loadPaymentsView() {
        try {
            const summary = await api.getPaymentSummary();
            document.getElementById('paySummaryToday').textContent = summary.today_collected_formatted;
            document.getElementById('paySummaryMonth').textContent = summary.month_collected_formatted;
            document.getElementById('paySummaryDues').textContent = summary.total_dues_formatted;

            const payments = await api.getPayments();
            const tbody = document.getElementById('paymentsTableBody');
            if (tbody) {
                if (payments.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 24px;">No fee collection records found.</td></tr>`;
                } else {
                    tbody.innerHTML = payments.map(p => views.renderPaymentRow(p)).join('');
                }
            }
        } catch (err) {
            console.error('Error loading payments view:', err);
        }
    },

    // --- Expenses View ---
    async loadExpensesView() {
        try {
            const summary = await api.getExpenseSummary();
            document.getElementById('expSummaryToday').textContent = summary.today_expenses_formatted;
            document.getElementById('expSummaryMonth').textContent = summary.month_expenses_formatted;
            document.getElementById('expSummaryTotal').textContent = summary.total_expenses_formatted;

            const expenses = await api.getExpenses();
            const tbody = document.getElementById('expensesTableBody');
            if (tbody) {
                if (expenses.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 24px;">No expense records found.</td></tr>`;
                } else {
                    tbody.innerHTML = expenses.map(e => views.renderExpenseRow(e)).join('');
                }
            }
        } catch (err) {
            console.error('Expenses error:', err);
        }
    },

    openAddExpenseModal() {
        document.getElementById('addExpenseForm').reset();
        document.getElementById('expenseDateInput').value = new Date().toISOString().split('T')[0];
        this.openModal('addExpenseModal');
    },

    async submitAddExpense(e) {
        e.preventDefault();
        const data = {
            category: document.getElementById('expenseCategorySelect').value,
            amount: parseFloat(document.getElementById('expenseAmountInput').value) || 0,
            date: document.getElementById('expenseDateInput').value || null,
            description: document.getElementById('expenseDescInput').value.trim() || null,
            paid_by: document.getElementById('expensePaidByInput').value.trim() || 'Admin'
        };

        if (data.amount <= 0) {
            this.showToast('Please specify a valid expense amount', 'error');
            return;
        }

        try {
            await api.addExpense(data);
            this.closeModal('addExpenseModal');
            this.showToast('Expense recorded successfully', 'success');
            await this.loadExpensesView();
        } catch (err) {
            this.showToast(err.message || 'Failed to record expense', 'error');
        }
    },

    // --- Trainers & Staff View ---
    async loadTrainersAndStaff() {
        try {
            const trainers = await api.getTrainers();
            const staff = await api.getStaff();

            const trainerContainer = document.getElementById('trainersGridContainer');
            if (trainerContainer) {
                trainerContainer.innerHTML = trainers.map(t => views.renderTrainerCard(t)).join('');
            }

            const staffTbody = document.getElementById('staffTableBody');
            if (staffTbody) {
                staffTbody.innerHTML = staff.map(s => views.renderStaffRow(s)).join('');
            }
        } catch (err) {
            console.error('Error loading trainers & staff:', err);
        }
    },

    openAddStaffModal() {
        document.getElementById('staffForm').reset();
        document.getElementById('staffJoinDateInput').value = new Date().toISOString().split('T')[0];
        this.openModal('staffModal');
    },

    async submitStaffForm(e) {
        e.preventDefault();
        const data = {
            staff_id: document.getElementById('staffIdInput').value.trim(),
            name: document.getElementById('staffNameInput').value.trim(),
            phone: document.getElementById('staffPhoneInput').value.trim(),
            cnic: document.getElementById('staffCnicInput').value.trim() || null,
            role: document.getElementById('staffRoleSelect').value,
            salary: parseFloat(document.getElementById('staffSalaryInput').value) || 0,
            joining_date: document.getElementById('staffJoinDateInput').value,
            status: 'Active'
        };

        try {
            await api.addStaff(data);
            this.closeModal('staffModal');
            this.showToast('Staff member added successfully', 'success');
            await this.loadTrainersAndStaff();
        } catch (err) {
            this.showToast(err.message || 'Failed to add staff member', 'error');
        }
    },

    // --- Reports View ---
    async loadReportsView(timeframe = 'month') {
        try {
            const fin = await api.getFinancialReport(timeframe);
            document.getElementById('repIncome').textContent = fin.summary.total_income_formatted;
            document.getElementById('repExpenses').textContent = fin.summary.total_expenses_formatted;
            document.getElementById('repNetProfit').textContent = fin.summary.net_profit_formatted;
            document.getElementById('repOutstanding').textContent = fin.summary.outstanding_dues_formatted;

            // Payment Methods list
            const methodList = document.getElementById('repIncomeMethodsList');
            if (methodList) {
                methodList.innerHTML = fin.income_by_method.map(m => `
                    <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-light);">
                        <span>${m.method}:</span>
                        <span style="font-weight: 700; color: var(--primary);">${m.amount_formatted}</span>
                    </div>
                `).join('') || '<div style="color: var(--text-dim);">No income records</div>';
            }

            // Expense categories list
            const catList = document.getElementById('repExpenseCatsList');
            if (catList) {
                catList.innerHTML = fin.expenses_by_category.map(c => `
                    <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-light);">
                        <span>${c.category}:</span>
                        <span style="font-weight: 700; color: var(--accent-rose);">${c.amount_formatted}</span>
                    </div>
                `).join('') || '<div style="color: var(--text-dim);">No expense records</div>';
            }

            // Membership summary
            const memRep = await api.getMembershipReport();
            document.getElementById('repTotalMem').textContent = memRep.total_members;
            document.getElementById('repActiveMem').textContent = memRep.active_members;
            document.getElementById('repExpiredMem').textContent = memRep.expired_members;
            document.getElementById('repRenewalsMonth').textContent = memRep.renewals_this_month;

            // Attendance leaderboard
            const attRep = await api.getAttendanceReport();
            const leaderTbody = document.getElementById('repAttendanceLeaderboardBody');
            if (leaderTbody) {
                leaderTbody.innerHTML = attRep.leaderboard.map((row, idx) => `
                    <tr>
                        <td style="font-weight: 700; color: var(--accent-amber);">#${idx + 1}</td>
                        <td style="font-weight: 600; color: #fff;">${row.name}</td>
                        <td>${row.phone}</td>
                        <td>${row.plan}</td>
                        <td><span class="badge badge-active">${row.visits} Visits</span></td>
                    </tr>
                `).join('') || '<tr><td colspan="5" style="text-align: center; color: var(--text-dim);">No check-in history</td></tr>';
            }
        } catch (err) {
            console.error('Reports view error:', err);
        }
    },

    printReport() {
        window.print();
    },

    // --- Settings View ---
    async loadSettingsView() {
        try {
            const s = await api.getSettings();
            document.getElementById('setGymName').value = s.gym_name || '';
            document.getElementById('setGymAddress').value = s.gym_address || '';
            document.getElementById('setGymPhone').value = s.gym_phone || '';
            document.getElementById('setCurrencySymbol').value = s.currency_symbol || 'Rs.';
            document.getElementById('setDefaultFee').value = s.default_fee || 2500;
            document.getElementById('setWarningDays').value = s.warning_days || 7;
            document.getElementById('setReceiptFooter').value = s.receipt_footer || '';
        } catch (err) {
            console.error('Error loading settings:', err);
        }
    },

    async submitSettingsForm(e) {
        e.preventDefault();
        const data = {
            gym_name: document.getElementById('setGymName').value.trim(),
            gym_address: document.getElementById('setGymAddress').value.trim(),
            gym_phone: document.getElementById('setGymPhone').value.trim(),
            currency_symbol: document.getElementById('setCurrencySymbol').value.trim(),
            default_fee: parseFloat(document.getElementById('setDefaultFee').value) || 2500,
            warning_days: parseInt(document.getElementById('setWarningDays').value) || 7,
            receipt_footer: document.getElementById('setReceiptFooter').value.trim()
        };

        try {
            await api.updateSettings(data);
            this.state.settings = await api.getSettings();
            this.updateBrandingUI();
            this.showToast('Settings saved successfully', 'success');
        } catch (err) {
            this.showToast(err.message || 'Failed to save settings', 'error');
        }
    },


    async deleteMember(memberId) {
        if (!confirm('Are you sure you want to deactivate this member? (Their financial and attendance history will be safely preserved).')) {
            return;
        }
        try {
            const res = await api.deleteMember(memberId);
            this.showToast(res.message, 'success');
            await this.loadMembers();
        } catch (err) {
            this.showToast(err.message || 'Failed to deactivate member', 'error');
        }
    }
};

// Start application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
