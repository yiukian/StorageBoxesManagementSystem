"""Primary layout and entry view for BoxVault application."""
import reflex as rx
from box_vault.state import AuthState, InventoryState, rxState
from box_vault.components.auth_view import auth_view
from box_vault.components.sidebar import sidebar
from box_vault.components.header import header
from box_vault.components.box_card import render_box_card
from box_vault.components.admin_panel import admin_panel
from box_vault.components.modals import (
    create_box_dialog,
    add_item_dialog,
    create_user_dialog,
    edit_user_dialog,
)


def empty_inventory_view() -> rx.Component:
    """Renders informative empty states when no boxes exist or search yields no matches."""
    return rx.center(
        rx.cond(
            InventoryState.total_boxes == 0,
            # No boxes created yet
            rx.card(
                rx.vstack(
                    rx.box(
                        rx.icon("package-plus", size=48, color="var(--indigo-9)"),
                        padding="4",
                        background="var(--indigo-3)",
                        border_radius="full",
                    ),
                    rx.heading("No Storage Boxes Created", size="5", weight="bold"),
                    rx.text(
                        "You haven't added any physical storage boxes yet. Create your first box to begin tracking your items.",
                        size="2",
                        color_scheme="gray",
                        text_align="center",
                        max_width="400px",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("plus", size=18),
                            rx.text("Create Your First Box"),
                            spacing="2",
                            align="center",
                        ),
                        size="3",
                        color_scheme="indigo",
                        on_click=InventoryState.open_create_box,
                    ),
                    spacing="3",
                    align="center",
                    padding="6",
                ),
                variant="surface",
                max_width="500px",
                width="100%",
                margin_y="8",
            ),
            # Search query yielded no matching boxes or items
            rx.card(
                rx.vstack(
                    rx.box(
                        rx.icon("search-x", size=48, color="var(--gray-9)"),
                        padding="4",
                        background="var(--gray-3)",
                        border_radius="full",
                    ),
                    rx.heading("No Matching Boxes or Items", size="5", weight="bold"),
                    rx.text(
                        "No boxes, locations, or items matched your current search term. Try a broader search keyword or clear the filter.",
                        size="2",
                        color_scheme="gray",
                        text_align="center",
                        max_width="400px",
                    ),
                    rx.button(
                        "Clear Search Filter",
                        variant="soft",
                        color_scheme="gray",
                        on_click=lambda: InventoryState.set_search_query(""),
                    ),
                    spacing="3",
                    align="center",
                    padding="6",
                ),
                variant="surface",
                max_width="500px",
                width="100%",
                margin_y="8",
            ),
        ),
        width="100%",
    )


def inventory_view() -> rx.Component:
    """The main storage boxes grid view for authenticated users."""
    return rx.vstack(
        # Top Subheader Summary
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.heading("Storage Inventory", size="6", weight="bold"),
                    rx.badge(
                        rx.hstack(
                            rx.icon("boxes", size=14),
                            rx.text(InventoryState.total_boxes, " Boxes"),
                            spacing="1",
                            align="center",
                        ),
                        color_scheme="indigo",
                        size="2",
                    ),
                    rx.badge(
                        rx.hstack(
                            rx.icon("layers", size=14),
                            rx.text(InventoryState.total_items, " Items"),
                            spacing="1",
                            align="center",
                        ),
                        color_scheme="teal",
                        size="2",
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.cond(
                    InventoryState.search_query != "",
                    rx.hstack(
                        rx.text(
                            "Filtering by: ",
                            rx.text.strong(InventoryState.search_query),
                            size="2",
                            color_scheme="gray",
                        ),
                        rx.button(
                            "Clear Filter",
                            size="1",
                            variant="ghost",
                            color_scheme="indigo",
                            on_click=lambda: InventoryState.set_search_query(""),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Manage your physical storage boxes and track their items.",
                        size="2",
                        color_scheme="gray",
                    ),
                ),
                spacing="1",
            ),
            align="center",
            width="100%",
            margin_bottom="4",
        ),

        # Responsive Box Grid
        rx.cond(
            InventoryState.filtered_boxes.length() > 0,
            rx.grid(
                rx.foreach(InventoryState.filtered_boxes, render_box_card),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="4",
                width="100%",
            ),
            empty_inventory_view(),
        ),
        spacing="4",
        width="100%",
    )


def dashboard_layout() -> rx.Component:
    """Primary application layout for authenticated users with sidebar and header."""
    return rx.hstack(
        # Navigation Sidebar
        sidebar(),

        # Main Scrollable Content Area
        rx.vstack(
            # Sticky Header with Search & New Box Button
            header(),

            # Dynamic View Content (Inventory vs Admin Panel)
            rx.box(
                rx.cond(
                    rxState.active_tab == "admin",
                    admin_panel(),
                    inventory_view(),
                ),
                padding_x="6",
                padding_y="5",
                width="100%",
                max_width="1400px",
                margin_x="auto",
            ),
            spacing="0",
            flex="1",
            height="100vh",
            overflow_y="auto",
        ),
        spacing="0",
        width="100%",
        min_height="100vh",
    )


def index() -> rx.Component:
    """Root view component: conditionally renders public auth landing or private dashboard."""
    return rx.box(
        rx.cond(
            AuthState.is_authenticated,
            dashboard_layout(),
            auth_view(),
        ),
        # Application modal dialogs available across views
        create_box_dialog(),
        add_item_dialog(),
        create_user_dialog(),
        edit_user_dialog(),
        width="100%",
        min_height="100vh",
    )
