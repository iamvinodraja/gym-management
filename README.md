# Pakistani Gym Management System

A modern, fast, simple, and practical **Gym Management System** designed specifically for small and medium-sized gyms in Pakistan. Replaces registers, diaries, notebooks, and manual fee calculations with a clean, responsive digital workspace for gym owners and receptionists.

---

## Key Features & Pakistani Localization

- **Currency & Formatting**: All amounts in Pakistani Rupees (`Rs. 2,500`).
- **Dates**: Standard Pakistani `DD-MM-YYYY` format.
- **Pakistani Identifiers**: Supports Pakistani phone formats (`03xx-xxxxxxx`) and CNICs (`xxxxx-xxxxxxx-x`).
- **Payment Methods**: Cash, Easypaisa, JazzCash, Bank Transfer.
- **Partial Payments & Dues**: Tracks outstanding dues per member automatically.
- **1-Click WhatsApp Reminders**: Direct `wa.me/92...` link with pre-filled polite reminder text for dues & renewals.
- **Printable Thermal & Voucher Receipts**: Instant print slip with gym branding, tax/receipt number, member details, paid/remaining balances, and custom footer rules.
- **Receptionist Attendance**: Rapid member search, 1-click Check-in and Check-out, and duplicate check-in protection for the same day.
- **Safe Financial Auditing**: Deleting a member deactivates the membership while preserving historical payments and attendance logs.
- **Dual Database Flexibility**: Native MySQL support with automatic seamless local SQLite fallback.

---

## Project Structure

```
gym-management/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app & static file mounting
│   │   ├── database.py              # Database engine (MySQL + SQLite fallback)
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── routes/                  # API endpoints (members, attendance, payments, etc.)
│   │   └── services/                # Business logic (ID generation, dues, receipts, auth)
│   ├── seed_data.py                 # Realistic Pakistani sample data seeder
│   └── requirements.txt             # Backend dependencies
├── frontend/
│   ├── index.html                   # Responsive dashboard interface
│   ├── css/
│   │   ├── style.css                # Dark gym aesthetic & responsive design
│   │   └── print.css                # Thermal slip & receipt print styles
│   └── js/
│       ├── api.js                   # API communication layer
│       ├── views.js                 # HTML component renderers
│       └── app.js                   # State, search, modals & workflow logic
├── database.sql                     # Pure MySQL schema & seed script
├── .env.example                     # Environment configuration template
├── .env                             # Active environment configuration
├── run.sh                           # One-click startup launcher
└── README.md                        # Documentation
```

---

## Quick Start

### 1. Requirements
- Python 3.9+
- MySQL (Optional, if not configured the system automatically runs on local SQLite)

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Configure Database (.env)
Edit `.env` if you want to connect directly to your local MySQL database:
```env
DATABASE_TYPE=auto
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password_here
MYSQL_DATABASE=gym_management
```
*(If MySQL password is blank or unreachable, it will seamlessly fall back to local `backend/gym_management.db` without crashing).*

Alternatively, to import directly into MySQL via CLI:
```bash
mysql -u root -p < database.sql
```

### 4. Run the System
```bash
./run.sh
```
Or manually:
```bash
python3 backend/seed_data.py
python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## Default Logins

| Role | Username | Password | Access Level |
|---|---|---|---|
| **Admin / Owner** | `admin` | `admin123` | Full Access (Settings, Expenses, Staff, Reports) |
| **Receptionist** | `reception` | `rec123` | Front Desk (Members, Attendance, Payments, Renewals) |

You can switch roles anytime by clicking the bottom-left profile widget.

---

## Core Receptionist Workflows

1. **Register Member**:
   Click `+ Add Member` on the top bar or Members page. Enter Name, Phone, select a Membership Plan (e.g. Monthly Regular Rs. 2,500), enter amount paid now, and select payment method (Cash, Easypaisa, JazzCash). The system generates Member ID (e.g. `PK-1007`) and opens the receipt voucher.

2. **Receptionist Check In**:
   Type the member's name or phone in the top search bar, or use the **Attendance** tab. Click **Check In**. If already checked in today, the system detects it and prompts for manual override.

3. **Renew Membership**:
   From Dashboard (Expiring Soon table) or Members list, click **Renew**. Select new plan, review fee and discount, enter amount paid, and save. The previous membership history is preserved and a new receipt is generated.

4. **Print Receipt**:
   Click **Slip** on any payment row. The system displays a thermal slip formatted with `Rs.` and your gym's footer note. Click **Print Receipt Slip** to print via thermal printer or standard A4.
