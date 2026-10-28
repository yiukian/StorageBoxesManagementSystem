"""State management for BoxVault (Storage Boxes Management System).

Contains centralized rx.State with modular sub-states for:
- AuthState: User session, registration, login, and first-time admin setup
- InventoryState: Boxes, items, instant keyword search, and counts
- AdminState: User account CRUD (create, amend, delete)
"""
import hashlib
import hmac
import os
from typing import Any, List, Optional
import reflex as rx
from sqlmodel import select, SQLModel

from box_vault.models import User, Box, Item


# ==============================================================================
# Security & Password Hashing Utilities (Pure Python Standard Library)
# ==============================================================================

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hashes a password with PBKDF2-HMAC-SHA256 and cryptographic salt."""
    if not salt:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    ).hex()
    return f"{salt}${hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plaintext password against the stored salt$hash string."""
    try:
        if not stored_hash or "$" not in stored_hash:
            return False
        salt, hash_val = stored_hash.split("$", 1)
        test_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        ).hex()
        return hmac.compare_digest(hash_val, test_hash)
    except Exception:
        return False


def ensure_db_initialized():
    """Ensures database tables are created and default admin is seeded."""
    with rx.session() as session:
        # Create all tables if not already existing
        SQLModel.metadata.create_all(session.get_bind())

        # Check if default admin account exists
        admin_user = session.exec(
            select(User).where(User.username == "admin")
        ).first()

        if not admin_user:
            # Seed default admin with empty password hash (triggers first-time setup)
            admin_user = User(
                username="admin",
                password_hash="",  # Unconfigured; requires setup on first login
                is_admin=True,
            )
            session.add(admin_user)
            session.commit()


# ==============================================================================
# Base State
# ==============================================================================

class rxState(rx.State):
    """Base application state providing global navigation and initialization."""
    active_tab: str = "inventory"  # "inventory" or "admin"

    def set_active_tab(self, tab: str):
        """Switches the active dashboard view."""
        self.active_tab = tab

    async def check_and_init(self):
        """Global on_load event handler to initialize DB and verify auth."""
        ensure_db_initialized()
        auth = await self.get_state(AuthState)
        auth.check_admin_status()
        if auth.is_authenticated:
            inv = await self.get_state(InventoryState)
            await inv.load_inventory()


# ==============================================================================
# Authentication State
# ==============================================================================

class AuthState(rxState):
    """Handles user sessions, authentication, and administrator first-time onboarding."""
    # Current active session data
    logged_in_user_id: int = -1
    logged_in_username: str = ""
    is_admin: bool = False

    # Auth UI view state ("login", "register", "admin_setup")
    auth_tab: str = "login"

    # Login form inputs
    login_username: str = ""
    login_password: str = ""

    # Registration form inputs
    register_username: str = ""
    register_password: str = ""
    register_confirm: str = ""

    # Administrator initial setup inputs
    admin_setup_password: str = ""
    admin_setup_confirm: str = ""

    # Feedback messages
    auth_error: str = ""
    auth_success: str = ""

    # Indicator if the default admin password is still pending setup
    admin_needs_first_time_setup: bool = False

    @rx.var
    def is_authenticated(self) -> bool:
        """Reactive boolean indicating if a valid user session exists."""
        return self.logged_in_user_id > 0

    def set_auth_tab(self, tab: str):
        """Switches between login, register, and admin setup forms."""
        self.auth_tab = tab
        self.auth_error = ""
        self.auth_success = ""

    def check_admin_status(self):
        """Checks if default administrator requires first-time password setup."""
        with rx.session() as session:
            admin_user = session.exec(
                select(User).where(User.username == "admin")
            ).first()
            if admin_user and (not admin_user.password_hash or admin_user.password_hash.strip() == ""):
                self.admin_needs_first_time_setup = True
            else:
                self.admin_needs_first_time_setup = False

    def login_user(self):
        """Authenticates a user by username and password."""
        self.auth_error = ""
        self.auth_success = ""

        username = self.login_username.strip()
        password = self.login_password

        if not username or not password:
            self.auth_error = "Please enter both username and password."
            return

        with rx.session() as session:
            user = session.exec(
                select(User).where(User.username == username)
            ).first()

            if not user:
                self.auth_error = "Invalid username or password."
                return

            # Check if this is the default admin logging in for the first time
            if user.username == "admin" and (not user.password_hash or user.password_hash.strip() == ""):
                self.admin_needs_first_time_setup = True
                self.auth_tab = "admin_setup"
                self.auth_success = "Default Admin detected! Please create your master password to complete setup."
                return

            # Verify password
            if not verify_password(password, user.password_hash):
                self.auth_error = "Invalid username or password."
                return

            # Login successful
            self.logged_in_user_id = user.id
            self.logged_in_username = user.username
            self.is_admin = user.is_admin
            self.login_password = ""
            self.auth_error = ""

        return [InventoryState.load_inventory, AdminState.load_users]

    def setup_first_time_admin(self):
        """Sets the master password for the default administrator account."""
        self.auth_error = ""
        self.auth_success = ""

        password = self.admin_setup_password
        confirm = self.admin_setup_confirm

        if not password or not confirm:
            self.auth_error = "Please enter and confirm your new administrator password."
            return

        if len(password) < 6:
            self.auth_error = "Administrator password must be at least 6 characters long."
            return

        if password != confirm:
            self.auth_error = "Passwords do not match."
            return

        with rx.session() as session:
            admin_user = session.exec(
                select(User).where(User.username == "admin")
            ).first()

            if not admin_user:
                admin_user = User(
                    username="admin",
                    password_hash=hash_password(password),
                    is_admin=True
                )
                session.add(admin_user)
            else:
                admin_user.password_hash = hash_password(password)
                admin_user.is_admin = True
                session.add(admin_user)

            session.commit()
            session.refresh(admin_user)

            # Auto-login the admin
            self.logged_in_user_id = admin_user.id
            self.logged_in_username = admin_user.username
            self.is_admin = True
            self.admin_needs_first_time_setup = False
            self.admin_setup_password = ""
            self.admin_setup_confirm = ""
            self.auth_tab = "login"

        return [InventoryState.load_inventory, AdminState.load_users]

    def register_user(self):
        """Registers a new standard user account."""
        self.auth_error = ""
        self.auth_success = ""

        username = self.register_username.strip()
        password = self.register_password
        confirm = self.register_confirm

        if not username or not password or not confirm:
            self.auth_error = "Please fill in all registration fields."
            return

        if len(username) < 3:
            self.auth_error = "Username must be at least 3 characters long."
            return

        if username.lower() == "admin":
            self.auth_error = "The username 'admin' is reserved for system administration."
            return

        if len(password) < 6:
            self.auth_error = "Password must be at least 6 characters long."
            return

        if password != confirm:
            self.auth_error = "Passwords do not match."
            return

        with rx.session() as session:
            existing_user = session.exec(
                select(User).where(User.username == username)
            ).first()

            if existing_user:
                self.auth_error = f"Username '{username}' is already taken."
                return

            new_user = User(
                username=username,
                password_hash=hash_password(password),
                is_admin=False
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            # Automatically log in the newly registered user
            self.logged_in_user_id = new_user.id
            self.logged_in_username = new_user.username
            self.is_admin = False
            self.register_username = ""
            self.register_password = ""
            self.register_confirm = ""

        return InventoryState.load_inventory

    def logout(self):
        """Terminates the current session and resets states."""
        self.logged_in_user_id = -1
        self.logged_in_username = ""
        self.is_admin = False
        self.login_username = ""
        self.login_password = ""
        self.auth_error = ""
        self.auth_success = ""
        self.auth_tab = "login"
        self.active_tab = "inventory"
        return [InventoryState.clear_inventory, AdminState.clear_admin]


# ==============================================================================
# Inventory Management State
# ==============================================================================

class InventoryState(rxState):
    """Manages physical storage boxes, items inside boxes, and live searching."""
    boxes: List[dict] = []
    search_query: str = ""

    # Box Creation Dialog Inputs
    new_box_name: str = ""
    new_box_location: str = ""
    is_create_box_open: bool = False

    # Add Item to Box Dialog Inputs
    add_item_box_id: int = -1
    add_item_box_name: str = ""
    new_item_name: str = ""
    new_item_quantity: int = 1
    new_item_description: str = ""
    is_add_item_open: bool = False

    # Notifications & errors
    inventory_error: str = ""
    inventory_success: str = ""

    @rx.var
    def total_boxes(self) -> int:
        """Returns total number of boxes owned by the user."""
        return len(self.boxes)

    @rx.var
    def total_items(self) -> int:
        """Returns total count of physical items across all boxes."""
        total = 0
        for box in self.boxes:
            total += int(box.get("item_count", 0))
        return total

    @rx.var
    def filtered_boxes(self) -> List[dict]:
        """Dynamically filters boxes and items by the sticky search bar keyword."""
        query = self.search_query.strip().lower()
        if not query:
            return self.boxes

        results = []
        for box in self.boxes:
            box_label = str(box.get("label_name", "")).lower()
            box_location = str(box.get("location", "")).lower()

            box_matches = query in box_label or query in box_location

            # Filter matching items inside the box
            matching_items = []
            for item in box.get("items", []):
                item_name = str(item.get("name", "")).lower()
                item_desc = str(item.get("description", "")).lower()
                if query in item_name or query in item_desc:
                    matching_items.append(item)

            if box_matches or matching_items:
                # Include box; if box itself matched, display all items, else display matching items
                filtered_box = dict(box)
                filtered_box["items"] = box["items"] if box_matches else matching_items
                filtered_box["item_count"] = len(filtered_box["items"])
                results.append(filtered_box)

        return results

    def set_search_query(self, query: str):
        """Updates instant search query as the user types."""
        self.search_query = query

    def clear_inventory(self):
        """Clears local inventory state on logout."""
        self.boxes = []
        self.search_query = ""

    async def load_inventory(self):
        """Fetches all boxes and nested items for the authenticated user."""
        auth = await self.get_state(AuthState)
        if not auth.is_authenticated:
            self.boxes = []
            return

        with rx.session() as session:
            # Query boxes owned by logged in user
            db_boxes = session.exec(
                select(Box)
                .where(Box.user_id == auth.logged_in_user_id)
                .order_by(Box.id.desc())
            ).all()

            boxes_data = []
            for b in db_boxes:
                # Fetch items for this box
                db_items = session.exec(
                    select(Item)
                    .where(Item.box_id == b.id)
                    .order_by(Item.id.asc())
                ).all()

                items_list = [
                    {
                        "id": item.id,
                        "name": item.name,
                        "quantity": item.quantity,
                        "description": item.description or "",
                        "box_id": item.box_id,
                    }
                    for item in db_items
                ]

                boxes_data.append({
                    "id": b.id,
                    "label_name": b.label_name,
                    "location": b.location or "General Storage",
                    "item_count": sum(i["quantity"] for i in items_list),
                    "items": items_list,
                })

            self.boxes = boxes_data

    # --- Box CRUD ---

    def open_create_box(self):
        """Opens the modal dialog to create a new storage box."""
        self.new_box_name = ""
        self.new_box_location = ""
        self.inventory_error = ""
        self.is_create_box_open = True

    def close_create_box(self):
        """Closes the create box modal."""
        self.is_create_box_open = False

    async def add_box(self):
        """Creates a new Box record in the database for the current user."""
        self.inventory_error = ""
        name = self.new_box_name.strip()
        location = self.new_box_location.strip()

        if not name:
            self.inventory_error = "Box Label Name is required."
            return

        auth = await self.get_state(AuthState)
        if not auth.is_authenticated:
            self.inventory_error = "User session expired. Please log in again."
            return

        with rx.session() as session:
            new_box = Box(
                label_name=name,
                location=location if location else "General Storage",
                user_id=auth.logged_in_user_id,
            )
            session.add(new_box)
            session.commit()

        self.is_create_box_open = False
        self.new_box_name = ""
        self.new_box_location = ""
        await self.load_inventory()

    async def delete_box(self, box_id: int):
        """Deletes a storage box and all items contained inside it."""
        auth = await self.get_state(AuthState)
        if not auth.is_authenticated:
            return

        with rx.session() as session:
            target_box = session.exec(
                select(Box).where(Box.id == box_id, Box.user_id == auth.logged_in_user_id)
            ).first()

            if target_box:
                # Delete items in box
                items = session.exec(select(Item).where(Item.box_id == box_id)).all()
                for item in items:
                    session.delete(item)
                # Delete box
                session.delete(target_box)
                session.commit()

        await self.load_inventory()

    # --- Item CRUD ---

    def open_add_item(self, box_id: int, box_name: str):
        """Opens the add item dialog targeted to a specific box."""
        self.add_item_box_id = box_id
        self.add_item_box_name = box_name
        self.new_item_name = ""
        self.new_item_quantity = 1
        self.new_item_description = ""
        self.inventory_error = ""
        self.is_add_item_open = True

    def close_add_item(self):
        """Closes the add item modal."""
        self.is_add_item_open = False

    def set_new_item_quantity(self, qty: str):
        """Safely parses and sets the item quantity input."""
        try:
            val = int(qty)
            self.new_item_quantity = max(1, val)
        except ValueError:
            self.new_item_quantity = 1

    async def add_item_to_box(self):
        """Inserts a new item into the specified storage box."""
        self.inventory_error = ""
        name = self.new_item_name.strip()
        desc = self.new_item_description.strip()
        qty = max(1, self.new_item_quantity)

        if not name:
            self.inventory_error = "Item Name cannot be empty."
            return

        if self.add_item_box_id <= 0:
            self.inventory_error = "No target box selected."
            return

        with rx.session() as session:
            new_item = Item(
                name=name,
                description=desc,
                quantity=qty,
                box_id=self.add_item_box_id,
            )
            session.add(new_item)
            session.commit()

        self.is_add_item_open = False
        self.new_item_name = ""
        self.new_item_description = ""
        self.new_item_quantity = 1
        await self.load_inventory()

    async def delete_item(self, item_id: int):
        """Removes a specific item from a box."""
        with rx.session() as session:
            item = session.exec(select(Item).where(Item.id == item_id)).first()
            if item:
                session.delete(item)
                session.commit()

        await self.load_inventory()

    async def quick_add_item(self, box_id: int, form_data: dict):
        """Quickly adds an item directly from the inline card input."""
        name = form_data.get("item_name", "").strip()
        qty_str = form_data.get("quantity", "1")
        try:
            qty = max(1, int(qty_str))
        except (ValueError, TypeError):
            qty = 1

        if not name:
            return

        with rx.session() as session:
            new_item = Item(
                name=name,
                description="",
                quantity=qty,
                box_id=box_id,
            )
            session.add(new_item)
            session.commit()

        await self.load_inventory()


# ==============================================================================
# Administrator User Management State
# ==============================================================================

class AdminState(rxState):
    """Provides Administrator privileges to list, create, amend, and delete user accounts."""
    users: List[dict] = []

    # Create User Modal state
    is_create_user_open: bool = False
    new_username: str = ""
    new_password: str = ""
    new_is_admin: bool = False

    # Amend/Edit User Modal state
    is_edit_user_open: bool = False
    edit_user_id: int = -1
    edit_username: str = ""
    edit_password: str = ""
    edit_is_admin: bool = False

    admin_error: str = ""
    admin_success: str = ""

    def clear_admin(self):
        """Resets admin state on logout."""
        self.users = []
        self.admin_error = ""
        self.admin_success = ""

    async def load_users(self):
        """Fetches all users with box and item statistics (Admin only)."""
        auth = await self.get_state(AuthState)
        if not auth.is_authenticated or not auth.is_admin:
            self.users = []
            return

        with rx.session() as session:
            all_users = session.exec(select(User).order_by(User.id.asc())).all()
            user_data = []

            for u in all_users:
                # Count boxes
                boxes = session.exec(select(Box).where(Box.user_id == u.id)).all()
                box_count = len(boxes)
                box_ids = [b.id for b in boxes]

                # Count items across user boxes
                item_count = 0
                if box_ids:
                    items = session.exec(select(Item).where(Item.box_id.in_(box_ids))).all()
                    item_count = sum(i.quantity for i in items)

                user_data.append({
                    "id": u.id,
                    "username": u.username,
                    "is_admin": u.is_admin,
                    "created_at": u.created_at or "N/A",
                    "box_count": box_count,
                    "item_count": item_count,
                })

            self.users = user_data

    # --- Create User ---

    def open_create_user(self):
        """Opens user creation modal."""
        self.new_username = ""
        self.new_password = ""
        self.new_is_admin = False
        self.admin_error = ""
        self.admin_success = ""
        self.is_create_user_open = True

    def close_create_user(self):
        """Closes user creation modal."""
        self.is_create_user_open = False

    def toggle_new_is_admin(self, value: bool):
        """Toggles administrator checkbox for new user."""
        self.new_is_admin = value

    async def create_user(self):
        """Creates a new user account with hashed password."""
        self.admin_error = ""
        username = self.new_username.strip()
        password = self.new_password

        if not username or not password:
            self.admin_error = "Username and password are required."
            return

        if len(password) < 6:
            self.admin_error = "Password must be at least 6 characters."
            return

        with rx.session() as session:
            existing = session.exec(select(User).where(User.username == username)).first()
            if existing:
                self.admin_error = f"Username '{username}' already exists."
                return

            user = User(
                username=username,
                password_hash=hash_password(password),
                is_admin=self.new_is_admin,
            )
            session.add(user)
            session.commit()

        self.is_create_user_open = False
        self.new_username = ""
        self.new_password = ""
        self.new_is_admin = False
        self.admin_success = f"User '{username}' created successfully."
        await self.load_users()

    # --- Amend/Edit User ---

    def open_edit_user(self, user_dict: dict):
        """Opens edit modal populated with existing user details."""
        self.edit_user_id = user_dict.get("id", -1)
        self.edit_username = user_dict.get("username", "")
        self.edit_password = ""  # Left empty unless admin desires to reset
        self.edit_is_admin = bool(user_dict.get("is_admin", False))
        self.admin_error = ""
        self.admin_success = ""
        self.is_edit_user_open = True

    def close_edit_user(self):
        """Closes user edit modal."""
        self.is_edit_user_open = False

    def toggle_edit_is_admin(self, value: bool):
        """Toggles administrator status during user editing."""
        self.edit_is_admin = value

    async def save_edit_user(self):
        """Amends user account details (username, role, and optional password reset)."""
        self.admin_error = ""
        if self.edit_user_id <= 0:
            return

        new_username = self.edit_username.strip()
        if not new_username:
            self.admin_error = "Username cannot be empty."
            return

        with rx.session() as session:
            user = session.exec(select(User).where(User.id == self.edit_user_id)).first()
            if not user:
                self.admin_error = "User not found."
                return

            # Check if username changed and conflicts
            if new_username != user.username:
                existing = session.exec(select(User).where(User.username == new_username)).first()
                if existing:
                    self.admin_error = f"Username '{new_username}' is already taken."
                    return
                user.username = new_username

            user.is_admin = self.edit_is_admin

            # If password field is filled, update password
            if self.edit_password.strip():
                if len(self.edit_password.strip()) < 6:
                    self.admin_error = "New password must be at least 6 characters."
                    return
                user.password_hash = hash_password(self.edit_password.strip())

            session.add(user)
            session.commit()

        self.is_edit_user_open = False
        self.edit_password = ""
        self.admin_success = f"User '{new_username}' amended successfully."
        await self.load_users()

    # --- Delete User ---

    async def delete_user(self, user_id: int):
        """Deletes a user account and purges their boxes and items."""
        self.admin_error = ""
        auth = await self.get_state(AuthState)

        # Prevent admin from deleting their own currently logged-in account
        if user_id == auth.logged_in_user_id:
            self.admin_error = "You cannot delete your own active administrator account."
            return

        with rx.session() as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                return

            # Delete all user's boxes and their items
            boxes = session.exec(select(Box).where(Box.user_id == user_id)).all()
            for b in boxes:
                items = session.exec(select(Item).where(Item.box_id == b.id)).all()
                for item in items:
                    session.delete(item)
                session.delete(b)

            session.delete(user)
            session.commit()

        self.admin_success = "User account removed."
        await self.load_users()
