"""Modal dialogs for box creation, item details, and administrative user controls."""
import reflex as rx
from box_vault.state import InventoryState, AdminState


def create_box_dialog() -> rx.Component:
    """Dialog modal to create a new storage box."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Create Storage Box"),
            rx.dialog.description(
                "Define a label name and physical storage location for your new box.",
                size="2",
                margin_bottom="4",
            ),
            rx.cond(
                InventoryState.inventory_error != "",
                rx.callout.root(
                    rx.callout.icon(rx.icon("circle-alert")),
                    rx.callout.text(InventoryState.inventory_error),
                    color_scheme="red",
                    size="1",
                    margin_bottom="3",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Box Label Name", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="e.g., Garage Tools, Winter Clothes #2",
                        value=InventoryState.new_box_name,
                        on_change=InventoryState.set_new_box_name,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Physical Location (Optional)", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="e.g., Shelf 3B, Attic Corner, Storage Unit A",
                        value=InventoryState.new_box_location,
                        on_change=InventoryState.set_new_box_location,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=InventoryState.close_create_box,
                    ),
                ),
                rx.button(
                    "Create Storage Box",
                    color_scheme="indigo",
                    on_click=InventoryState.add_box,
                ),
                spacing="3",
                justify="end",
                margin_top="5",
            ),
            max_width="450px",
        ),
        open=InventoryState.is_create_box_open,
    )


def add_item_dialog() -> rx.Component:
    """Detailed item dialog modal to add an item with full description."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Add Item to "),
                    rx.badge(InventoryState.add_item_box_name, color_scheme="indigo", size="2"),
                    spacing="2",
                    align="center",
                )
            ),
            rx.dialog.description(
                "Specify the item name, quantity, and notes or description.",
                size="2",
                margin_bottom="4",
            ),
            rx.cond(
                InventoryState.inventory_error != "",
                rx.callout.root(
                    rx.callout.icon(rx.icon("circle-alert")),
                    rx.callout.text(InventoryState.inventory_error),
                    color_scheme="red",
                    size="1",
                    margin_bottom="3",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Item Name", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="e.g., Phillips Screwdriver, HDMI Cable",
                        value=InventoryState.new_item_name,
                        on_change=InventoryState.set_new_item_name,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Quantity", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="Quantity",
                        type="number",
                        min="1",
                        value=InventoryState.new_item_quantity.to_string(),
                        on_change=InventoryState.set_new_item_quantity,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Description or Notes (Optional)", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="e.g., Black, 2 meters, tested working",
                        value=InventoryState.new_item_description,
                        on_change=InventoryState.set_new_item_description,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=InventoryState.close_add_item,
                    ),
                ),
                rx.button(
                    "Add Item",
                    color_scheme="indigo",
                    on_click=InventoryState.add_item_to_box,
                ),
                spacing="3",
                justify="end",
                margin_top="5",
            ),
            max_width="450px",
        ),
        open=InventoryState.is_add_item_open,
    )


def create_user_dialog() -> rx.Component:
    """Administrator dialog to create a new user account."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Create New User Account"),
            rx.dialog.description(
                "Create a user account with login credentials and assigned system role.",
                size="2",
                margin_bottom="4",
            ),
            rx.cond(
                AdminState.admin_error != "",
                rx.callout.root(
                    rx.callout.icon(rx.icon("circle-alert")),
                    rx.callout.text(AdminState.admin_error),
                    color_scheme="red",
                    size="1",
                    margin_bottom="3",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Username", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="Unique username",
                        value=AdminState.new_username,
                        on_change=AdminState.set_new_username,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Password", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="Temporary or initial password (min 6 chars)",
                        type="password",
                        value=AdminState.new_password,
                        on_change=AdminState.set_new_password,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.checkbox(
                        checked=AdminState.new_is_admin,
                        on_change=AdminState.toggle_new_is_admin,
                    ),
                    rx.text("Grant Administrator Privileges", size="2"),
                    spacing="2",
                    align="center",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.close_create_user,
                    ),
                ),
                rx.button(
                    "Create User",
                    color_scheme="indigo",
                    on_click=AdminState.create_user,
                ),
                spacing="3",
                justify="end",
                margin_top="5",
            ),
            max_width="450px",
        ),
        open=AdminState.is_create_user_open,
    )


def edit_user_dialog() -> rx.Component:
    """Administrator dialog to amend an existing user account."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Amend User Account"),
            rx.dialog.description(
                "Modify username, adjust permissions, or reset user password.",
                size="2",
                margin_bottom="4",
            ),
            rx.cond(
                AdminState.admin_error != "",
                rx.callout.root(
                    rx.callout.icon(rx.icon("circle-alert")),
                    rx.callout.text(AdminState.admin_error),
                    color_scheme="red",
                    size="1",
                    margin_bottom="3",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Username", size="2", font_weight="medium"),
                    rx.input(
                        value=AdminState.edit_username,
                        on_change=AdminState.set_edit_username,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Reset Password (Leave blank to keep existing)", size="2", font_weight="medium"),
                    rx.input(
                        placeholder="Enter new password to reset",
                        type="password",
                        value=AdminState.edit_password,
                        on_change=AdminState.set_edit_password,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.checkbox(
                        checked=AdminState.edit_is_admin,
                        on_change=AdminState.toggle_edit_is_admin,
                    ),
                    rx.text("Administrator Privileges", size="2"),
                    spacing="2",
                    align="center",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.close_edit_user,
                    ),
                ),
                rx.button(
                    "Save Changes",
                    color_scheme="indigo",
                    on_click=AdminState.save_edit_user,
                ),
                spacing="3",
                justify="end",
                margin_top="5",
            ),
            max_width="450px",
        ),
        open=AdminState.is_edit_user_open,
    )
