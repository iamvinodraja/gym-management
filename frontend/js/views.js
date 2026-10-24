/**
 * Views and HTML Template Renderers for Gym Management System
 */

const views = {
    renderMemberRow(m) {
        let badgeClass = 'badge-active';
        if (m.status === 'Expiring Soon') badgeClass = 'badge-expiring';
        else if (m.status === 'Expired') badgeClass = 'badge-expired';
        else if (m.status === 'Inactive') badgeClass = 'badge-inactive';

        const remainingText = m.remaining_days < 0 
            ? `<span style="color: var(--accent-rose); font-weight: 700;">${Math.abs(m.remaining_days)}d ago</span>` 
            : `${m.remaining_days} days`;

        const duesBadge = m.outstanding_amount > 0 
            ? `<span class="badge badge-due">${m.outstanding_formatted}</span>` 
            : `<span style="color: var(--text-dim);">Paid</span>`;

        // Format clean Pakistani phone link
        const cleanPhone = (m.phone || '').replace(/[^0-9]/g, '');
        const waNumber = cleanPhone.startsWith('0') ? '92' + cleanPhone.substring(1) : cleanPhone;
        const waMsg = encodeURIComponent(`Assalam-o-Alaikum ${m.full_name}, reminder regarding your membership at the gym. Expiry: ${m.expiry_date || 'N/A'}. Outstanding dues: ${m.outstanding_formatted}.`);

        return `
            <tr>
                <td><span class="member-code-badge">${m.member_id}</span></td>
                <td>
                    <div style="font-weight: 700; color: #fff;">${m.full_name}</div>
                    <div style="font-size: 11px; color: var(--text-dim);">${m.gender} ${m.cnic ? '• ' + m.cnic : ''}</div>
                </td>
                <td>
                    <a href="tel:${m.phone}" style="color: var(--text-main); text-decoration: none;">${m.phone}</a>
                </td>
                <td><span style="font-weight: 600;">${m.plan_name}</span></td>
                <td>${m.expiry_date || '-'}</td>
                <td><span class="badge ${badgeClass}">${m.status}</span></td>
                <td>${remainingText}</td>
                <td>${duesBadge}</td>
                <td>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        <button class="btn btn-secondary btn-sm" onclick="app.viewMemberProfile(${m.id})" title="View Profile">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="app.openRenewModal(${m.id})" title="Renew Plan">
                            <i class="fas fa-sync-alt"></i> Renew
                        </button>
                        <button class="btn btn-amber btn-sm" onclick="app.openPaymentModal(${m.id})" title="Receive Payment">
                            <i class="fas fa-money-bill-wave"></i> Pay
                        </button>
                        <button class="btn btn-cyan btn-sm btn-icon-only" onclick="app.quickCheckIn(${m.id})" title="Check In">
                            <i class="fas fa-sign-in-alt"></i>
                        </button>
                        ${waNumber ? `
                        <a href="https://wa.me/${waNumber}?text=${waMsg}" target="_blank" class="btn btn-whatsapp btn-sm btn-icon-only" title="Send WhatsApp Reminder">
                            <i class="fab fa-whatsapp"></i>
                        </a>` : ''}
                        <button class="btn btn-rose btn-sm btn-icon-only" onclick="app.deleteMember(${m.id})" title="Deactivate">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    renderTodayAttendanceRow(att) {
        if (!att) return '';
        const isCheckedOut = !!att.check_out_time && att.check_out_time !== '-';
        const memberId = att.member_id || 'N/A';
        const name = att.name || att.full_name || 'Unknown';
        const phone = att.phone || '';
        const checkIn = att.check_in || att.check_in_time || '-';
        const checkOut = att.check_out || att.check_out_time || '-';
        const status = att.status || 'Checked In';
        const attId = att.id || 0;

        return `
            <tr>
                <td><span class="member-code-badge">${memberId}</span></td>
                <td style="font-weight: 600; color: #fff;">${name}</td>
                <td style="color: var(--text-muted);">${phone}</td>
                <td><span style="color: var(--primary); font-weight: 700;">${checkIn}</span></td>
                <td>${isCheckedOut ? `<span style="color: var(--text-dim);">${checkOut}</span>` : '<span style="color: var(--accent-amber); font-weight: 600;">In Gym</span>'}</td>
                <td><span class="badge ${isCheckedOut ? 'badge-inactive' : 'badge-active'}">${status}</span></td>
                <td>
                    ${!isCheckedOut && attId ? `
                        <button class="btn btn-secondary btn-sm" onclick="app.checkOutAttendance(${attId})">
                            <i class="fas fa-sign-out-alt"></i> Check Out
                        </button>
                    ` : '<span style="color: var(--text-dim); font-size: 12px;">Completed</span>'}
                </td>
            </tr>
        `;
    },

    renderExpiringRow(m) {
        if (!m) return '';
        const name = m.name || m.full_name || 'Unknown';
        const phone = m.phone || '';
        const cleanPhone = phone.replace(/[^0-9]/g, '');
        const waNumber = cleanPhone.startsWith('0') ? '92' + cleanPhone.substring(1) : cleanPhone;
        const expiryDate = m.expiry_date || '-';
        const daysLeft = m.days_left !== undefined ? m.days_left : 0;
        const outstandingFormatted = m.outstanding_formatted || 'Rs. 0';
        const outstandingAmount = m.outstanding_amount || 0;
        const memberId = m.id || 0;

        const waMsg = encodeURIComponent(`Assalam-o-Alaikum ${name}, this is a reminder from Power Fitness Gym. Your gym membership expires on ${expiryDate} (${daysLeft} days left). Outstanding balance: ${outstandingFormatted}. Please visit the reception for renewal.`);

        return `
            <tr>
                <td>
                    <div style="font-weight: 700; color: #fff;">${name}</div>
                    <div style="font-size: 11px; color: var(--text-dim);">${phone}</div>
                </td>
                <td><span style="color: var(--accent-amber); font-weight: 700;">${expiryDate}</span></td>
                <td><span class="badge badge-expiring">${daysLeft} Days</span></td>
                <td>${outstandingAmount > 0 ? `<span class="badge badge-due">${outstandingFormatted}</span>` : '<span style="color: var(--primary);">Nil</span>'}</td>
                <td>
                    <div style="display: flex; gap: 6px;">
                        ${memberId ? `<button class="btn btn-primary btn-sm" onclick="app.openRenewModal(${memberId})">Renew</button>` : ''}
                        ${waNumber ? `
                            <a href="https://wa.me/${waNumber}?text=${waMsg}" target="_blank" class="btn btn-whatsapp btn-sm btn-icon-only" title="Send WhatsApp">
                                <i class="fab fa-whatsapp"></i>
                            </a>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    },

    renderPaymentRow(p) {
        if (!p) return '';
        const payId = p.payment_id || (p.id ? `REC-${p.id}` : 'REC');
        const memberName = p.member_name || 'N/A';
        const memberCode = p.member_code || '';
        const amountFormatted = p.amount_formatted || `Rs. ${p.amount || 0}`;
        const method = p.payment_method || 'Cash';
        const date = p.payment_date || p.date || '-';
        const receivedBy = p.received_by || 'Reception';
        const paymentDbId = p.id || 0;

        return `
            <tr>
                <td><span class="member-code-badge">${payId}</span></td>
                <td>
                    <div style="font-weight: 700; color: #fff;">${memberName}</div>
                    <div style="font-size: 11px; color: var(--text-dim);">${memberCode}</div>
                </td>
                <td style="font-weight: 800; color: var(--primary); font-size: 14px;">${amountFormatted}</td>
                <td><span class="badge badge-active">${method}</span></td>
                <td>${date}</td>
                <td style="color: var(--text-dim); font-size: 12px;">${receivedBy}</td>
                <td>
                    ${paymentDbId ? `
                        <button class="btn btn-secondary btn-sm" onclick="app.showReceipt(${paymentDbId})">
                            <i class="fas fa-receipt"></i> Slip
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    },

    renderPlanCard(plan) {
        return `
            <div class="plan-card">
                <div class="plan-header">
                    <div class="plan-name">${plan.name}</div>
                    <span class="badge ${plan.is_active ? 'badge-active' : 'badge-inactive'}">
                        ${plan.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
                <div class="plan-price">${plan.price_formatted}</div>
                <div class="plan-duration"><i class="fas fa-clock"></i> ${plan.duration_days > 0 ? plan.duration_days + ' Days Access' : 'One-time'}</div>
                <div class="plan-desc">${plan.description || 'Access to weight area and cardio equipment.'}</div>
                <div style="display: flex; gap: 8px; margin-top: auto;">
                    <button class="btn btn-outline btn-sm" style="flex: 1;" onclick="app.openEditPlanModal(${plan.id}, '${plan.name}', ${plan.duration_days}, ${plan.price}, '${(plan.description || '').replace(/'/g, "\\'")}', ${plan.is_active})">
                        <i class="fas fa-edit"></i> Edit Price
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="app.togglePlanActive(${plan.id}, ${!plan.is_active})">
                        ${plan.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                </div>
            </div>
        `;
    },

    renderExpenseRow(exp) {
        return `
            <tr>
                <td>${exp.date}</td>
                <td><span class="badge badge-expiring">${exp.category}</span></td>
                <td style="font-weight: 700; color: var(--accent-rose);">${exp.amount_formatted}</td>
                <td style="color: var(--text-muted);">${exp.description || '-'}</td>
                <td style="color: var(--text-dim); font-size: 12px;">${exp.paid_by || 'Admin'}</td>
            </tr>
        `;
    },

    renderStaffRow(s) {
        return `
            <tr>
                <td><span class="member-code-badge">${s.staff_id}</span></td>
                <td style="font-weight: 700; color: #fff;">${s.name}</td>
                <td>${s.phone}</td>
                <td style="color: var(--text-dim);">${s.cnic || '-'}</td>
                <td><span class="badge badge-active">${s.role}</span></td>
                <td style="font-weight: 700;">${s.salary_formatted}</td>
                <td>${s.joining_date}</td>
                <td><span class="badge ${s.status === 'Active' ? 'badge-active' : 'badge-inactive'}">${s.status}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="app.openEditStaffModal(${s.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="app.deleteStaff(${s.id})" title="Delete Staff" style="margin-left: 4px;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    },

    renderTrainerCard(t) {
        return `
            <div class="card-panel" style="padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <h3 style="font-size: 16px; font-weight: 700; color: #fff;">${t.name}</h3>
                        <p style="font-size: 12px; color: var(--primary); font-weight: 600;">${t.specialization}</p>
                    </div>
                    <span class="badge ${t.status === 'active' ? 'badge-active' : 'badge-inactive'}">${t.status}</span>
                </div>
                <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 8px;">
                    <i class="fas fa-phone"></i> ${t.phone}
                </div>
                <div style="display: flex; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 10px 14px; border-radius: var(--radius-md); margin-top: 14px;">
                    <div>
                        <div style="font-size: 11px; color: var(--text-dim);">Members</div>
                        <div style="font-size: 16px; font-weight: 700; color: #fff;">${t.assigned_members_count}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: var(--text-dim);">Salary</div>
                        <div style="font-size: 16px; font-weight: 700; color: var(--accent-cyan);">${t.salary_formatted}</div>
                    </div>
                </div>
            </div>
        `;
    },

    renderReceiptHTML(data) {
        return `
            <div class="receipt-paper">
                <div class="receipt-header">
                    <h2>${data.gym.name}</h2>
                    <p>${data.gym.address}</p>
                    <p>Phone: ${data.gym.phone}</p>
                </div>

                <div class="receipt-divider"></div>

                <div class="receipt-row">
                    <span>Receipt No:</span>
                    <span style="font-weight: bold;">${data.receipt.receipt_no}</span>
                </div>
                <div class="receipt-row">
                    <span>Date & Time:</span>
                    <span>${data.receipt.date} ${data.receipt.created_time}</span>
                </div>

                <div class="receipt-divider"></div>

                <div class="receipt-row">
                    <span>Member Name:</span>
                    <span style="font-weight: bold;">${data.member.name}</span>
                </div>
                <div class="receipt-row">
                    <span>Member ID:</span>
                    <span>${data.member.member_id}</span>
                </div>
                <div class="receipt-row">
                    <span>Membership Plan:</span>
                    <span>${data.member.plan_name}</span>
                </div>
                <div class="receipt-row">
                    <span>Valid Expiry:</span>
                    <span>${data.member.expiry_date || 'N/A'}</span>
                </div>

                <div class="receipt-divider"></div>

                <div class="receipt-row bold">
                    <span>Amount Paid:</span>
                    <span style="font-size: 16px;">${data.amount.paid_formatted}</span>
                </div>
                ${data.amount.discount > 0 ? `
                <div class="receipt-row">
                    <span>Discount:</span>
                    <span>${data.amount.discount_formatted}</span>
                </div>` : ''}
                <div class="receipt-row">
                    <span>Payment Method:</span>
                    <span>${data.receipt.payment_method}</span>
                </div>
                <div class="receipt-row" style="color: ${data.member.remaining_balance > 0 ? '#b91c1c' : '#047857'}; font-weight: bold;">
                    <span>Remaining Balance:</span>
                    <span>${data.member.remaining_balance_formatted}</span>
                </div>

                <div class="receipt-divider"></div>

                <div class="receipt-row">
                    <span>Received By:</span>
                    <span>${data.receipt.received_by}</span>
                </div>

                <div class="receipt-footer">
                    <p>${data.gym.footer}</p>
                    <p style="margin-top: 6px;">*** Keep this slip for verification ***</p>
                </div>
            </div>
        `;
    }
};
