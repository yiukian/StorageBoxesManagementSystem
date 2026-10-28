"""Sidebar navigation and quick statistics component for authenticated users."""
import reflex as rx
from box_vault.state import AuthState, InventoryState, rxState


def sidebar() -> rx.Component:
    """Renders the left navigation sidebar with user profile and inventory statistics."""
    return rx.vstack(
        # App Branding Header
        rx.hstack(
            rx.box(
                rx.icon("box", size=24, color="var(--indigo-9)"),
                padding="2",
                background="var(--indigo-3)",
                border_radius="10px",
            ),
            rx.vstack(
                rx.heading("BoxVault", size="5", weight="bold"),
                rx.text("Storage Manager", size="1", color_scheme="gray"),
                spacing="0",
            ),
            spacing="3",
            align="center",
            width="100%",
            padding_bottom="4",
        ),

        rx.separator(width="100%"),

        # User Profile Snapshot
        rx.card(
            rx.hstack(
                rx.box(
                    rx.icon("user", size=20, color="var(--accent-9)"),
                    padding="2",
                    background="var(--accent-3)",
                    border_radius="full",
                ),
                rx.vstack(
                    rx.text(
                        AuthState.logged_in_username,
                        font_weight="bold",
                        size="2",
                        truncate=True,
                        max_width="120px",
                    ),
                    rx.cond(
                        AuthState.is_admin,
                        rx.badge(
                            rx.hstack(
                                rx.icon("shield-check", size=12),
                                rx.text("Admin", size="1"),
                                spacing="1",
                                align="center",
                            ),
                            color_scheme="amber",
                            size="1",
                            radius="full",
                        ),
                        rx.badge("Member", color_scheme="indigo", size="1", radius="full"),
                    ),
                    spacing="1",
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            variant="surface",
        ),

        # Navigation Links
        rx.vstack(
            rx.button(
                rx.hstack(
                    rx.icon("archive", size=18),
                    rx.text("Storage Boxes"),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                variant=rx.cond(rxState.active_tab == "inventory", "solid", "ghost"),
                color_scheme="indigo",
                justify="start",
                on_click=lambda: rxState.set_active_tab("inventory"),
            ),
            rx.cond(
                AuthState.is_admin,
                rx.button(
                    rx.hstack(
                        rx.icon("users", size=18),
                        rx.text("User Accounts"),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    variant=rx.cond(rxState.active_tab == "admin", "solid", "ghost"),
                    color_scheme="indigo",
                    justify="start",
                    on_click=lambda: rxState.set_active_tab("admin"),
                ),
                rx.fragment(),
            ),
            spacing="2",
            width="100%",
            margin_top="3",
        ),

        # Quick Statistics Card
        rx.card(
            rx.vstack(
                rx.text("Quick Inventory Stats", size="1", font_weight="bold", color_scheme="gray"),
                rx.hstack(
                    rx.box(
                        rx.icon("boxes", size=20, color="var(--indigo-9)"),
                        padding="2",
                        background="var(--indigo-3)",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.text("Total Boxes", size="1", color_scheme="gray"),
                        rx.text(InventoryState.total_boxes, size="4", font_weight="bold"),
                        spacing="0",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
                rx.hstack(
                    rx.box(
                        rx.icon("layers", size=20, color="var(--teal-9)"),
                        padding="2",
                        background="var(--teal-3)",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.text("Total Items", size="1", color_scheme="gray"),
                        rx.text(InventoryState.total_items, size="4", font_weight="bold"),
                        spacing="0",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
            margin_top="auto",
        ),

        rx.separator(width="100%"),

        # Log Out Button
        rx.button(
            rx.hstack(
                rx.icon("log-out", size=16),
                rx.text("Sign Out"),
                spacing="2",
                align="center",
            ),
            variant="ghost",
            color_scheme="red",
            width="100%",
            justify="start",
            on_click=AuthState.logout,
        ),
        spacing="4",
        padding="5",
        height="100vh",
        width="260px",
        border_right="1px solid var(--gray-4)",
        background="var(--card-background)",
    )
