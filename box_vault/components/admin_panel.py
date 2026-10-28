"""Administrator User Management view for managing user accounts."""
import reflex as rx
from box_vault.models import UserView
from box_vault.state import AdminState, AuthState


def render_user_row(user: UserView) -> rx.Component:
    """Renders a single user row in the administrative user list."""
    return rx.card(
        rx.hstack(
            # Avatar & Username Info
            rx.hstack(
                rx.box(
                    rx.icon("user", size=18, color="var(--indigo-9)"),
                    padding="2",
                    background="var(--indigo-3)",
                    border_radius="full",
                ),
                rx.vstack(
                    rx.text(user.username, font_weight="bold", size="3"),
                    rx.text("Created: ", user.created_at, size="1", color_scheme="gray"),
                    spacing="0",
                ),
                spacing="3",
                align="center",
                flex="2",
            ),

            # Role Badge
            rx.box(
                rx.cond(
                    user.is_admin,
                    rx.badge(
                        rx.hstack(
                            rx.icon("shield-check", size=12),
                            rx.text("Administrator", size="1"),
                            spacing="1",
                            align="center",
                        ),
                        color_scheme="amber",
                        variant="solid",
                    ),
                    rx.badge("Standard Member", color_scheme="indigo", variant="soft"),
                ),
                flex="1",
            ),

            # Stats (Boxes & Items owned)
            rx.hstack(
                rx.badge(
                    rx.hstack(
                        rx.icon("box", size=12),
                        rx.text(user.box_count, " boxes"),
                        spacing="1",
                        align="center",
                    ),
                    variant="surface",
                    color_scheme="gray",
                ),
                rx.badge(
                    rx.hstack(
                        rx.icon("layers", size=12),
                        rx.text(user.item_count, " items"),
                        spacing="1",
                        align="center",
                    ),
                    variant="surface",
                    color_scheme="gray",
                ),
                spacing="2",
                flex="1.5",
            ),

            # Action Buttons: Amend & Delete
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("pencil", size=14),
                        rx.text("Amend", size="2"),
                        spacing="1",
                        align="center",
                    ),
                    variant="soft",
                    color_scheme="indigo",
                    size="2",
                    on_click=lambda: AdminState.open_edit_user(user),
                ),
                rx.cond(
                    user.id != AuthState.logged_in_user_id,
                    rx.icon_button(
                        rx.icon("trash-2", size=16),
                        variant="ghost",
                        color_scheme="red",
                        size="2",
                        cursor="pointer",
                        title="Delete User",
                        on_click=lambda: AdminState.delete_user(user.id),
                    ),
                    rx.badge("Active Session", size="1", color_scheme="gray", variant="outline"),
                ),
                spacing="2",
                align="center",
            ),
            align="center",
            width="100%",
        ),
        variant="surface",
        width="100%",
        padding="3",
    )


def admin_panel() -> rx.Component:
    """Administrator panel for user account management."""
    return rx.vstack(
        # Admin Header & Actions
        rx.hstack(
            rx.vstack(
                rx.heading("User Account Management", size="6", weight="bold"),
                rx.text(
                    "Administrator controls to create, amend, and delete user accounts.",
                    size="2",
                    color_scheme="gray",
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon("user-plus", size=18),
                    rx.text("Create New User"),
                    spacing="2",
                    align="center",
                ),
                color_scheme="indigo",
                size="3",
                on_click=AdminState.open_create_user,
            ),
            align="center",
            width="100%",
            margin_bottom="4",
        ),

        # Status and Alert Messages
        rx.cond(
            AdminState.admin_error != "",
            rx.callout.root(
                rx.callout.icon(rx.icon("circle-alert")),
                rx.callout.text(AdminState.admin_error),
                color_scheme="red",
                width="100%",
                margin_bottom="3",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AdminState.admin_success != "",
            rx.callout.root(
                rx.callout.icon(rx.icon("circle-check")),
                rx.callout.text(AdminState.admin_success),
                color_scheme="green",
                width="100%",
                margin_bottom="3",
            ),
            rx.fragment(),
        ),

        # User List
        rx.vstack(
            rx.foreach(AdminState.users, render_user_row),
            spacing="3",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )
