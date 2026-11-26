"""State management for BoxVault (Storage Boxes Management System).

Contains centralized rx.State with modular sub-states for:
- AuthState: User session, registration, login, and first-time admin setup
- InventoryState: Boxes, items, multi-user sharing, soft-delete archiving, and collaborative guards
- AdminState: User account CRUD (create, amend, delete)
"""
import hashlib
import hmac
import os
from typing import List, Optional
import reflex as rx
from sqlmodel import select, or_, col, SQLModel

from box_vault.models import User, Box, Item, BoxAccess, ItemView, BoxView, UserView


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

    def set_login_username(self, val: str):
        self.login_username = val

    def set_login_password(self, val: str):
        self.login_password = val

    def set_register_username(self, val: str):
        self.register_username = val

    def set_register_password(self, val: str):
        self.register_password = val

    def set_register_confirm(self, val: str):
        self.register_confirm = val

    def set_admin_setup_password(self, val: str):
        self.admin_setup_password = val

    def set_admin_setup_confirm(self, val: str):
        self.admin_setup_confirm = val

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
    """Manages physical storage boxes, items inside boxes, sharing, and soft-delete archiving."""
    boxes: List[BoxView] = []
    search_query: str = ""

    # Active vs. Archived Boxes View Toggle
    show_archived: bool = False

    # Stats for active authorized inventory
    total_active_boxes: int = 0
    total_active_items: int = 0

    # Box Creation Dialog Inputs
    new_box_name: str = ""
    new_box_location: str = ""
    is_public: bool = True  # Bound to UI Switch: "Make Public (Visible to all users)"
    shared_with_usernames: str = ""  # Comma-separated usernames if not public
    is_create_box_open: bool = False

    # Box Editing Dialog Inputs (Collaborative editing)
    edit_box_id: int = -1
    edit_box_name: str = ""
    edit_box_location: str = ""
    edit_box_is_public: bool = True
    edit_box_shared_with: str = ""
    is_edit_box_open: bool = False

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
        """Returns total number of active authorized boxes accessible to the user."""
        return self.total_active_boxes

    @rx.var
    def total_items(self) -> int:
        """Returns total count of physical items across active authorized boxes."""
        return self.total_active_items

    @rx.var
    def filtered_boxes(self) -> List[BoxView]:
        """Dynamically filters boxes and items by the sticky search bar keyword."""
        query = self.search_query.strip().lower()
        if not query:
            return self.boxes

        results: List[BoxView] = []
        for box in self.boxes:
            box_label = box.label_name.lower()
            box_location = box.location.lower()
            box_owner = box.owner_username.lower()

            box_matches = query in box_label or query in box_location or query in box_owner

            # Filter matching items inside the box
            matching_items = [
                item for item in box.box_items
                if query in item.name.lower() or query in item.description.lower()
            ]

            if box_matches or matching_items:
                items_to_show = box.box_items if box_matches else matching_items
                results.append(
                    BoxView(
                        id=box.id,
                        label_name=box.label_name,
                        location=box.location,
                        owner_id=box.owner_id,
                        owner_username=box.owner_username,
                        is_public=box.is_public,
                        is_archived=box.is_archived,
                        item_count=sum(i.quantity for i in items_to_show),
                        box_items=items_to_show,
                        access_type=box.access_type,
                        shared_with_usernames=box.shared_with_usernames,
                        is_owner=box.is_owner,
                    )
                )

        return results

    def set_search_query(self, query: str):
        """Updates instant search query as the user types."""
        self.search_query = query

    async def toggle_show_archived(self):
        """Toggles between Active Boxes and Archived Boxes views."""
        self.show_archived = not self.show_archived
        await self.load_inventory()

    async def set_show_archived(self, show: bool):
        """Sets the active archive view flag and reloads inventory."""
        self.show_archived = show
        await self.load_inventory()

    def clear_inventory(self):
        """Clears local inventory state on logout."""
        self.boxes = []
        self.search_query = ""
        self.show_archived = False
        self.total_active_boxes = 0
        self.total_active_items = 0

    # --- Collaborative Access Helper ---

    def _has_box_access(self, box_id: int, user_id: int) -> bool:
        """Helper method verifying if a user has view/edit/delete access to a box.

        Access is granted if:
        1. User is the creator/owner (box.owner_id == user_id)
        2. Box is public (box.is_public == True)
        3. User is explicitly linked via BoxAccess link table
        """
        if user_id <= 0 or box_id <= 0:
            return False

        with rx.session() as session:
            target_box = session.exec(select(Box).where(Box.id == box_id)).first()
            if not target_box:
                return False

            # Owner has full access
            if target_box.owner_id == user_id:
                return True

            # Public boxes are accessible to all authenticated users
            if target_box.is_public:
                return True

            # Explicit BoxAccess sharing
            access = session.exec(
                select(BoxAccess).where(
                    BoxAccess.box_id == box_id,
                    BoxAccess.user_id == user_id
                )
            ).first()
            return access is not None

    async def load_inventory(self):
        """Fetches all boxes and nested items authorized for the authenticated user.

        A user ONLY sees boxes where:
        Box.owner_id == current_user_id OR Box.is_public == True OR current_user_id is in BoxAccess.
        Respects Box.is_archived == self.show_archived.
        """
        auth = await self.get_state(AuthState)
        if not auth.is_authenticated:
            self.boxes = []
            self.total_active_boxes = 0
            self.total_active_items = 0
            return

        current_user_id = auth.logged_in_user_id

        with rx.session() as session:
            # Query IDs of boxes explicitly shared with the user
            shared_box_ids = session.exec(
                select(BoxAccess.box_id).where(BoxAccess.user_id == current_user_id)
            ).all()

            # Condition matching authorized boxes
            auth_filter = or_(
                Box.owner_id == current_user_id,
                Box.is_public == True,
                col(Box.id).in_(shared_box_ids) if shared_box_ids else False
            )

            # Compute active inventory statistics for sidebar
            active_boxes = session.exec(
                select(Box).where(auth_filter, Box.is_archived == False)
            ).all()
            self.total_active_boxes = len(active_boxes)

            active_box_ids = [b.id for b in active_boxes]
            if active_box_ids:
                active_items = session.exec(
                    select(Item).where(col(Item.box_id).in_(active_box_ids))
                ).all()
                self.total_active_items = sum(i.quantity for i in active_items)
            else:
                self.total_active_items = 0

            # Fetch boxes matching the current show_archived view
            db_boxes = session.exec(
                select(Box)
                .where(auth_filter, Box.is_archived == self.show_archived)
                .order_by(Box.id.desc())
            ).all()

            boxes_data: List[BoxView] = []
            for b in db_boxes:
                # Fetch items for this box
                db_items = session.exec(
                    select(Item)
                    .where(Item.box_id == b.id)
                    .order_by(Item.id.asc())
                ).all()

                items_list = [
                    ItemView(
                        id=item.id,
                        name=item.name,
                        quantity=item.quantity,
                        description=item.description or "",
                        box_id=item.box_id,
                    )
                    for item in db_items
                ]

                # Fetch box creator username
                owner_user = session.exec(select(User).where(User.id == b.owner_id)).first()
                owner_name = owner_user.username if owner_user else "Unknown"

                # Fetch explicit shared usernames
                shared_usernames = session.exec(
                    select(User.username)
                    .join(BoxAccess, BoxAccess.user_id == User.id)
                    .where(BoxAccess.box_id == b.id)
                ).all()

                if b.is_public:
                    access_type = "Public"
                elif shared_usernames:
                    access_type = "Shared"
                else:
                    access_type = "Private"

                boxes_data.append(
                    BoxView(
                        id=b.id,
                        label_name=b.label_name,
                        location=b.location or "General Storage",
                        owner_id=b.owner_id,
                        owner_username=owner_name,
                        is_public=b.is_public,
                        is_archived=b.is_archived,
                        item_count=sum(i.quantity for i in items_list),
                        box_items=items_list,
                        access_type=access_type,
                        shared_with_usernames=", ".join(shared_usernames),
                        is_owner=(b.owner_id == current_user_id),
                    )
                )

            self.boxes = boxes_data

    # --- Box Input Setters ---

    def set_new_box_name(self, val: str):
        self.new_box_name = val

    def set_new_box_location(self, val: str):
        self.new_box_location = val

    def set_is_public(self, val: bool):
        self.is_public = val

    def toggle_is_public(self, val: bool):
        self.is_public = val

    def set_shared_with_usernames(self, val: str):
        self.shared_with_usernames = val

    def set_new_item_name(self, val: str):
        self.new_item_name = val

    def set_new_item_description(self, val: str):
        self.new_item_description = val

    def open_create_box(self):
        """Opens the modal dialog to create a new storage box."""
        self.new_box_name = ""
        self.new_box_location = ""
        self.is_public = True
        self.shared_with_usernames = ""
        self.inventory_error = ""
        self.is_create_box_open = True

    def close_create_box(self):
        """Closes the create box modal."""
        self.is_create_box_open = False

    # --- Box Creation ---

    async def add_box(
        self,
        name: str = "",
        location: str = "",
        is_public: bool = True,
        shared_with_usernames: str = "",
    ):
        """Creates a new Box record owned by the currently authenticated user.

        If is_public is False and shared_with_usernames is provided, creates BoxAccess records.
        """
        self.inventory_error = ""

        # Default to state variables if called from Reflex UI without direct arguments
        box_name = name.strip() if name else self.new_box_name.strip()
        box_location = location.strip() if location else self.new_box_location.strip()
        box_is_public = is_public if name else self.is_public
        box_shared_with = shared_with_usernames if name else self.shared_with_usernames

        if not box_name:
            self.inventory_error = "Box Label Name is required."
            return

        auth = await self.get_state(AuthState)
        if not auth.is_authenticated:
            self.inventory_error = "User session expired. Please log in again."
            return

        current_user_id = auth.logged_in_user_id

        with rx.session() as session:
            new_box = Box(
                label_name=box_name,
                location=box_location if box_location else "General Storage",
                owner_id=current_user_id,
                is_public=box_is_public,
                is_archived=False,
            )
            session.add(new_box)
            session.commit()
            session.refresh(new_box)

            # If private/shared, link specified usernames via BoxAccess
            if not box_is_public and box_shared_with.strip():
                targets = [u.strip() for u in box_shared_with.split(",") if u.strip()]
                for target_username in targets:
                    target_user = session.exec(
                        select(User).where(User.username == target_username)
                    ).first()
                    if target_user and target_user.id != current_user_id:
                        session.add(BoxAccess(user_id=target_user.id, box_id=new_box.id))
                session.commit()

        self.is_create_box_open = False
        self.new_box_name = ""
        self.new_box_location = ""
        self.is_public = True
        self.shared_with_usernames = ""
        await self.load_inventory()

    # --- Box Editing (Collaborative) ---

    def open_edit_box(self, box: BoxView):
        """Opens edit modal for an authorized user to modify box details."""
        self.edit_box_id = box.id
        self.edit_box_name = box.label_name
        self.edit_box_location = box.location
        self.edit_box_is_public = box.is_public
        self.edit_box_shared_with = box.shared_with_usernames
        self.inventory_error = ""
        self.is_edit_box_open = True

    def close_edit_box(self):
        """Closes the edit box modal."""
        self.is_edit_box_open = False

    def set_edit_box_name(self, val: str):
        self.edit_box_name = val

    def set_edit_box_location(self, val: str):
        self.edit_box_location = val

    def set_edit_box_is_public(self, val: bool):
        self.edit_box_is_public = val

    def toggle_edit_box_is_public(self, val: bool):
        self.edit_box_is_public = val

    def set_edit_box_shared_with(self, val: str):
        self.edit_box_shared_with = val

    async def edit_box(
        self,
        box_id: int = -1,
        name: str = "",
        location: str = "",
        is_public: Optional[bool] = None,
        shared_with_usernames: Optional[str] = None,
    ):
        """Amends box metadata after verifying collaborative permission guards."""
        target_id = box_id if box_id > 0 else self.edit_box_id
        auth = await self.get_state(AuthState)

        # Collaborative guard check
        if not self._has_box_access(target_id, auth.logged_in_user_id):
            return rx.window_alert("Unauthorized action")

        new_name = name.strip() if name else self.edit_box_name.strip()
        new_loc = location.strip() if location else self.edit_box_location.strip()
        new_pub = is_public if is_public is not None else self.edit_box_is_public
        new_shared = shared_with_usernames if shared_with_usernames is not None else self.edit_box_shared_with

        if not new_name:
            self.inventory_error = "Box Label Name cannot be empty."
            return

        with rx.session() as session:
            box = session.exec(select(Box).where(Box.id == target_id)).first()
            if not box:
                return

            box.label_name = new_name
            box.location = new_loc if new_loc else "General Storage"
            box.is_public = new_pub

            # Update shared users via BoxAccess link table
            old_accesses = session.exec(select(BoxAccess).where(BoxAccess.box_id == target_id)).all()
            for oa in old_accesses:
                session.delete(oa)

            if not new_pub and new_shared.strip():
                targets = [u.strip() for u in new_shared.split(",") if u.strip()]
                for target_username in targets:
                    target_user = session.exec(
                        select(User).where(User.username == target_username)
                    ).first()
                    if target_user and target_user.id != box.owner_id:
                        session.add(BoxAccess(user_id=target_user.id, box_id=target_id))

            session.add(box)
            session.commit()

        self.is_edit_box_open = False
        await self.load_inventory()

    # --- Soft-Delete (Archive) & Restore Box ---

    async def delete_box(self, box_id: int):
        """Soft-deletes (archives) a storage box after checking collaborative permissions.

        Preserves the box and all its items in the database by setting is_archived = True.
        """
        auth = await self.get_state(AuthState)
        if not self._has_box_access(box_id, auth.logged_in_user_id):
            return rx.window_alert("Unauthorized action")

        with rx.session() as session:
            target_box = session.exec(select(Box).where(Box.id == box_id)).first()
            if target_box:
                target_box.is_archived = True
                session.add(target_box)
                session.commit()

        await self.load_inventory()

    async def restore_box(self, box_id: int):
        """Restores a soft-deleted (archived) storage box back to active inventory."""
        auth = await self.get_state(AuthState)
        if not self._has_box_access(box_id, auth.logged_in_user_id):
            return rx.window_alert("Unauthorized action")

        with rx.session() as session:
            target_box = session.exec(select(Box).where(Box.id == box_id)).first()
            if target_box:
                target_box.is_archived = False
                session.add(target_box)
                session.commit()

        await self.load_inventory()

    # --- Item CRUD (Collaborative Guards) ---

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
        """Inserts a new item into the box after verifying collaborative permissions."""
        self.inventory_error = ""
        auth = await self.get_state(AuthState)

        # Collaborative permission guard
        if not self._has_box_access(self.add_item_box_id, auth.logged_in_user_id):
            return rx.window_alert("Unauthorized action")

        name = self.new_item_name.strip()
        desc = self.new_item_description.strip()
        qty = max(1, self.new_item_quantity)

        if not name:
            self.inventory_error = "Item Name cannot be empty."
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

    async def quick_add_item(self, box_id: int, form_data: dict):
        """Quickly adds an item directly from the inline card input after permission check."""
        auth = await self.get_state(AuthState)

        # Collaborative permission guard
        if not self._has_box_access(box_id, auth.logged_in_user_id):
            return rx.window_alert("Unauthorized action")

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

    async def delete_item(self, item_id: int):
        """Removes a specific item after verifying collaborative access to the parent box."""
        auth = await self.get_state(AuthState)

        with rx.session() as session:
            item = session.exec(select(Item).where(Item.id == item_id)).first()
            if not item:
                return

            # Collaborative permission guard on parent box
            if not self._has_box_access(item.box_id, auth.logged_in_user_id):
                return rx.window_alert("Unauthorized action")

            session.delete(item)
            session.commit()

        await self.load_inventory()


# ==============================================================================
# Administrator User Management State
# ==============================================================================

class AdminState(rxState):
    """Provides Administrator privileges to list, create, amend, and delete user accounts."""
    users: List[UserView] = []

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
            user_data: List[UserView] = []

            for u in all_users:
                # Count boxes owned by this user
                boxes = session.exec(select(Box).where(Box.owner_id == u.id)).all()
                box_count = len(boxes)
                box_ids = [b.id for b in boxes]

                # Count items across user's owned boxes
                item_count = 0
                if box_ids:
                    items = session.exec(select(Item).where(col(Item.box_id).in_(box_ids))).all()
                    item_count = sum(i.quantity for i in items)

                user_data.append(
                    UserView(
                        id=u.id,
                        username=u.username,
                        is_admin=u.is_admin,
                        created_at=u.created_at or "N/A",
                        box_count=box_count,
                        item_count=item_count,
                    )
                )

            self.users = user_data

    def set_new_username(self, val: str):
        self.new_username = val

    def set_new_password(self, val: str):
        self.new_password = val

    def set_edit_username(self, val: str):
        self.edit_username = val

    def set_edit_password(self, val: str):
        self.edit_password = val

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

    def open_edit_user(self, user: UserView):
        """Opens edit modal populated with existing user details."""
        self.edit_user_id = user.id
        self.edit_username = user.username
        self.edit_password = ""  # Left empty unless admin desires to reset
        self.edit_is_admin = user.is_admin
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
        """Deletes a user account and purges their owned boxes and items."""
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

            # Remove BoxAccess links for this user
            user_accesses = session.exec(select(BoxAccess).where(BoxAccess.user_id == user_id)).all()
            for ua in user_accesses:
                session.delete(ua)

            # Delete all user's owned boxes, their items, and any BoxAccess links
            boxes = session.exec(select(Box).where(Box.owner_id == user_id)).all()
            for b in boxes:
                # Delete items
                items = session.exec(select(Item).where(Item.box_id == b.id)).all()
                for item in items:
                    session.delete(item)
                # Delete BoxAccess entries for this box
                box_accesses = session.exec(select(BoxAccess).where(BoxAccess.box_id == b.id)).all()
                for ba in box_accesses:
                    session.delete(ba)
                session.delete(b)

            session.delete(user)
            session.commit()

        self.admin_success = "User account removed."
        await self.load_users()
