# BoxVault — Storage Boxes Management System

A production-grade, functional web application built with **100% pure Python** using **Reflex** (formerly Pynecone) and **SQLModel** (SQLite).

---

## 📁 Modular Directory Structure

```text
StorageBoxesManagementSystem/
├── rxconfig.py                     # Reflex application configuration & DB connection
├── requirements.txt                # Python dependencies
├── README.md                       # Documentation & execution instructions
└── box_vault/                      # Main application package
    ├── __init__.py                 # Package declaration
    ├── box_vault.py                # Main app entrypoint, theme & page routing
    ├── models.py                   # SQLModel entities (User, Box, Item)
    ├── state.py                    # Centralized rxState with Auth, Inventory, and Admin sub-states
    ├── index.py                    # Top-level index re-export
    ├── pages/
    │   ├── __init__.py
    │   └── index.py                # Primary responsive UI layout & conditional rendering
    └── components/
        ├── __init__.py
        ├── auth_view.py            # Welcome hero, Login, Register, & Admin Setup cards
        ├── sidebar.py              # Navigation, user profile, and live inventory stats
        ├── header.py               # Sticky search bar & "+ New Box" modal trigger
        ├── box_card.py             # Physical box cards with scrollable items & inline add form
        ├── admin_panel.py          # Administrator user management (create, amend, delete)
        └── modals.py               # Creation & editing dialog modals
```

---

## 🚀 Key Features

1. **Pure Python Architecture**:
   - Zero raw JavaScript, CSS, or HTML files.
   - Built entirely on Reflex's component layout primitives (`rx.vstack`, `rx.hstack`, `rx.card`, `rx.grid`, `rx.scroll_area`).
   - 100% reactive conditionals using `rx.cond(...)` and iterative loops using `rx.foreach(...)`.

2. **Session Security & User Authentication**:
   - Standard library PBKDF2-HMAC-SHA256 password hashing with unique 16-byte random salts.
   - Session tracking via `AuthState.logged_in_user_id`.
   - Access restriction: unauthenticated users only see the landing page and authentication card; all dashboard and inventory operations are strictly blocked without a session.

3. **First-Time Administrator Setup**:
   - An administrator user (`admin`) is automatically seeded in the database with an empty initial password.
   - On first visit/login, the system detects this state and prompts the administrator to configure a secure master password.
   - Once configured, the administrator gains access to the **User Management Panel** to create, amend (change roles, reset passwords), and delete user accounts.

4. **Physical Storage Boxes & Inventory Tracking**:
   - Users create boxes with custom label names and physical locations (e.g. *"Garage Shelf 3B"*).
   - Each box card displays:
     - Box title, location pill, and total item counter.
     - Scrollable list of items with quantities and individual trash bin icons.
     - Inline quick-add item form combo (`Item name`, `Qty`, `+`).
     - Detailed edit modal for adding items with rich descriptions.
     - Complete box deletion with cascading item cleanup.

5. **Sticky Global Live Search**:
   - Live search bar in the sticky header updates results instantaneously as the user types.
   - Queries match against box label names, storage locations, item names, and item descriptions.

---

## 🛠️ Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Reflex
```bash
reflex init
```

### 3. Run the Development Server
```bash
reflex run
```

Access the application in your browser at `http://localhost:3000`. The backend Reflex server runs automatically at `http://localhost:8000`.

---

## 🔑 Default Administrator Credentials

- **Username**: `admin`
- **First-time Login**: The system will prompt you to set your administrator master password on initial login.
