"""Box card component representing physical storage boxes and their contained items.

Supports public/shared/private badges, collaborative editing/deleting, and soft-delete archiving.
"""
import reflex as rx
from box_vault.models import ItemView, BoxView
from box_vault.state import InventoryState


def render_item_row(item: ItemView) -> rx.Component:
    """Renders an individual item row inside a storage box with delete action (hidden if archived)."""
    return rx.hstack(
        rx.badge(
            rx.text(item.quantity, size="1", font_weight="bold"),
            color_scheme="indigo",
            variant="solid",
            size="1",
            radius="large",
        ),
        rx.vstack(
            rx.text(
                item.name,
                size="2",
                font_weight="medium",
                line_clamp=1,
            ),
            rx.cond(
                item.description != "",
                rx.text(
                    item.description,
                    size="1",
                    color_scheme="gray",
                    line_clamp=1,
                ),
                rx.fragment(),
            ),
            spacing="0",
            flex="1",
        ),
        # In archived mode, delete item action is hidden (read-only)
        rx.cond(
            ~InventoryState.show_archived,
            rx.icon_button(
                rx.icon("trash-2", size=13),
                size="1",
                variant="ghost",
                color_scheme="red",
                cursor="pointer",
                title="Delete Item",
                on_click=lambda: InventoryState.delete_item(item.id),
            ),
            rx.fragment(),
        ),
        align="center",
        spacing="2",
        padding_y="1",
        padding_x="2",
        border_radius="6px",
        background="var(--gray-2)",
        width="100%",
    )


def box_access_badge(box: BoxView) -> rx.Component:
    """Renders the appropriate visibility badge (Public, Shared, or Private, plus Archived)."""
    return rx.cond(
        box.is_archived,
        rx.badge(
            rx.hstack(
                rx.icon("archive", size=11),
                rx.text("Archived", size="1"),
                spacing="1",
                align="center",
            ),
            color_scheme="amber",
            variant="solid",
            size="1",
        ),
        rx.cond(
            box.is_public,
            rx.badge(
                rx.hstack(
                    rx.icon("globe", size=11),
                    rx.text("Public", size="1"),
                    spacing="1",
                    align="center",
                ),
                color_scheme="green",
                variant="soft",
                size="1",
            ),
            rx.cond(
                box.access_type == "Shared",
                rx.badge(
                    rx.hstack(
                        rx.icon("users", size=11),
                        rx.text("Shared", size="1"),
                        spacing="1",
                        align="center",
                    ),
                    color_scheme="blue",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    rx.hstack(
                        rx.icon("lock", size=11),
                        rx.text("Private", size="1"),
                        spacing="1",
                        align="center",
                    ),
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
            ),
        ),
    )


def render_box_card(box: BoxView) -> rx.Component:
    """Renders a responsive card representing a physical storage box with collaborative controls."""
    return rx.card(
        rx.vstack(
            # Top Header: Box Title, Badges, and Action Buttons (Edit, Archive / Restore)
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.icon(
                            rx.cond(box.is_archived, "archive", "box"),
                            size=18,
                            color=rx.cond(box.is_archived, "var(--amber-9)", "var(--indigo-9)"),
                        ),
                        padding="1.5",
                        background=rx.cond(box.is_archived, "var(--amber-3)", "var(--indigo-3)"),
                        border_radius="6px",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.heading(
                                box.label_name,
                                size="4",
                                weight="bold",
                                line_clamp=1,
                            ),
                            box_access_badge(box),
                            spacing="2",
                            align="center",
                        ),
                        # Subtle Created by label
                        rx.text(
                            "Created by: ",
                            rx.text.strong(box.owner_username),
                            size="1",
                            color_scheme="gray",
                        ),
                        spacing="0",
                    ),
                    spacing="2",
                    align="center",
                    flex="1",
                ),

                # Collaborative Action Controls:
                rx.hstack(
                    # Active mode: Collaborative Edit Box button
                    rx.cond(
                        ~InventoryState.show_archived,
                        rx.icon_button(
                            rx.icon("pencil", size=15),
                            size="2",
                            variant="ghost",
                            color_scheme="indigo",
                            cursor="pointer",
                            title="Edit Box Details",
                            on_click=lambda: InventoryState.open_edit_box(box),
                        ),
                        rx.fragment(),
                    ),
                    # Active mode: Soft-Delete (Archive) Box button
                    rx.cond(
                        ~InventoryState.show_archived,
                        rx.icon_button(
                            rx.icon("archive", size=15),
                            size="2",
                            variant="ghost",
                            color_scheme="amber",
                            cursor="pointer",
                            title="Archive Box (Soft-Delete)",
                            on_click=lambda: InventoryState.delete_box(box.id),
                        ),
                        # Archived mode: Restore Box button
                        rx.button(
                            rx.hstack(
                                rx.icon("archive-restore", size=14),
                                rx.text("Restore", size="1"),
                                spacing="1",
                                align="center",
                            ),
                            size="1",
                            color_scheme="green",
                            variant="soft",
                            cursor="pointer",
                            title="Restore Box to Active",
                            on_click=lambda: InventoryState.restore_box(box.id),
                        ),
                    ),
                    spacing="1",
                    align="center",
                ),
                align="center",
                width="100%",
            ),

            # Metadata Pill Badges (Location and Total Count)
            rx.hstack(
                rx.badge(
                    rx.hstack(
                        rx.icon("map-pin", size=12),
                        rx.text(box.location, size="1"),
                        spacing="1",
                        align="center",
                    ),
                    variant="soft",
                    color_scheme="gray",
                    size="1",
                ),
                rx.badge(
                    rx.hstack(
                        rx.icon("layers", size=12),
                        rx.text(box.item_count, " items", size="1"),
                        spacing="1",
                        align="center",
                    ),
                    variant="soft",
                    color_scheme="indigo",
                    size="1",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),

            rx.separator(width="100%"),

            # Scrollable List of Box Contents
            rx.scroll_area(
                rx.cond(
                    box.item_count > 0,
                    rx.vstack(
                        rx.foreach(box.box_items, render_item_row),
                        spacing="2",
                        width="100%",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("inbox", size=24, color="var(--gray-7)"),
                            rx.text("Box is currently empty", size="2", color_scheme="gray"),
                            spacing="1",
                            align="center",
                            padding_y="4",
                        ),
                        width="100%",
                    ),
                ),
                type="auto",
                scrollbars="vertical",
                style={"height": 160},
                width="100%",
            ),

            rx.separator(width="100%"),

            # Inline "Add Item" Form Combo (Only shown in active mode; read-only if archived)
            rx.cond(
                ~InventoryState.show_archived,
                rx.form(
                    rx.hstack(
                        rx.input(
                            name="item_name",
                            placeholder="Quick item name...",
                            size="2",
                            flex="1",
                            required=True,
                        ),
                        rx.input(
                            name="quantity",
                            placeholder="Qty",
                            default_value="1",
                            type="number",
                            min="1",
                            size="2",
                            width="55px",
                        ),
                        rx.button(
                            rx.icon("plus", size=16),
                            type="submit",
                            size="2",
                            color_scheme="indigo",
                            title="Add item quickly",
                        ),
                        rx.icon_button(
                            rx.icon("pencil", size=15),
                            variant="soft",
                            size="2",
                            color_scheme="gray",
                            cursor="pointer",
                            title="Add with details/description",
                            on_click=lambda: InventoryState.open_add_item(box.id, box.label_name),
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    on_submit=lambda form_data: InventoryState.quick_add_item(box.id, form_data),
                    reset_on_submit=True,
                    width="100%",
                ),
                rx.hstack(
                    rx.icon("lock", size=14, color="var(--gray-8)"),
                    rx.text("Archived Box (Read-Only)", size="1", color_scheme="gray"),
                    spacing="1",
                    align="center",
                    justify="center",
                    width="100%",
                    padding_y="1",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        variant="surface",
        border_radius="12px",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
        opacity=rx.cond(InventoryState.show_archived, "0.85", "1"),
        width="100%",
    )
