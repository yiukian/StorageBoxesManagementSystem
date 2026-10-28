"""Authentication and landing view for unauthenticated visitors."""
import reflex as rx
from box_vault.state import AuthState


def auth_alerts() -> rx.Component:
    """Renders contextual success and error message alerts."""
    return rx.vstack(
        rx.cond(
            AuthState.auth_error != "",
            rx.callout.root(
                rx.callout.icon(rx.icon("circle-alert")),
                rx.callout.text(AuthState.auth_error),
                color_scheme="red",
                role="alert",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AuthState.auth_success != "",
            rx.callout.root(
                rx.callout.icon(rx.icon("circle-check")),
                rx.callout.text(AuthState.auth_success),
                color_scheme="green",
                role="status",
                width="100%",
            ),
            rx.fragment(),
        ),
        spacing="2",
        width="100%",
    )


def admin_first_run_callout() -> rx.Component:
    """Highlights to the administrator if first-time password setup is required."""
    return rx.cond(
        AuthState.admin_needs_first_time_setup,
        rx.callout.root(
            rx.callout.icon(rx.icon("shield-alert")),
            rx.vstack(
                rx.text(
                    "Administrator Setup Required",
                    font_weight="bold",
                    size="2",
                ),
                rx.text(
                    "Default Administrator account is uninitialized. Configure your master password to enable administrative controls.",
                    size="2",
                ),
                rx.button(
                    "Set Admin Password Now",
                    size="1",
                    variant="soft",
                    color_scheme="amber",
                    on_click=lambda: AuthState.set_auth_tab("admin_setup"),
                ),
                spacing="2",
                align="start",
            ),
            color_scheme="amber",
            width="100%",
            margin_bottom="3",
        ),
        rx.fragment(),
    )


def login_form() -> rx.Component:
    """The standard username and password login form."""
    return rx.vstack(
        rx.vstack(
            rx.text("Username", size="2", font_weight="medium"),
            rx.input(
                placeholder="Enter your username",
                value=AuthState.login_username,
                on_change=AuthState.set_login_username,
                width="100%",
                size="3",
            ),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("Password", size="2", font_weight="medium"),
            rx.input(
                placeholder="Enter your password",
                type="password",
                value=AuthState.login_password,
                on_change=AuthState.set_login_password,
                width="100%",
                size="3",
            ),
            spacing="1",
            width="100%",
        ),
        rx.button(
            rx.hstack(
                rx.icon("log-in", size=18),
                rx.text("Sign In to BoxVault"),
                spacing="2",
                align="center",
            ),
            size="3",
            width="100%",
            color_scheme="indigo",
            on_click=AuthState.login_user,
        ),
        rx.hstack(
            rx.text("Don't have an account?", size="2", color_scheme="gray"),
            rx.button(
                "Register here",
                variant="ghost",
                size="2",
                color_scheme="indigo",
                on_click=lambda: AuthState.set_auth_tab("register"),
            ),
            spacing="1",
            align="center",
            justify="center",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def register_form() -> rx.Component:
    """Registration form for new members."""
    return rx.vstack(
        rx.vstack(
            rx.text("Desired Username", size="2", font_weight="medium"),
            rx.input(
                placeholder="Choose a unique username",
                value=AuthState.register_username,
                on_change=AuthState.set_register_username,
                width="100%",
                size="3",
            ),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("Password", size="2", font_weight="medium"),
            rx.input(
                placeholder="At least 6 characters",
                type="password",
                value=AuthState.register_password,
                on_change=AuthState.set_register_password,
                width="100%",
                size="3",
            ),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("Confirm Password", size="2", font_weight="medium"),
            rx.input(
                placeholder="Re-enter your password",
                type="password",
                value=AuthState.register_confirm,
                on_change=AuthState.set_register_confirm,
                width="100%",
                size="3",
            ),
            spacing="1",
            width="100%",
        ),
        rx.button(
            rx.hstack(
                rx.icon("user-plus", size=18),
                rx.text("Create Account"),
                spacing="2",
                align="center",
            ),
            size="3",
            width="100%",
            color_scheme="teal",
            on_click=AuthState.register_user,
        ),
        rx.hstack(
            rx.text("Already registered?", size="2", color_scheme="gray"),
            rx.button(
                "Sign In",
                variant="ghost",
                size="2",
                color_scheme="indigo",
                on_click=lambda: AuthState.set_auth_tab("login"),
            ),
            spacing="1",
            align="center",
            justify="center",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def admin_setup_form() -> rx.Component:
    """First-time password setup form for default Administrator."""
    return rx.vstack(
        rx.card(
            rx.hstack(
                rx.icon("shield-check", size=24, color="var(--amber-9)"),
                rx.vstack(
                    rx.text("Initialize Master Administrator", font_weight="bold", size="3"),
                    rx.text(
                        "Set a secure password for the default 'admin' account. This will complete the one-time administrator onboarding.",
                        size="2",
                        color_scheme="gray",
                    ),
                    spacing="1",
                ),
                spacing="3",
                align="center",
            ),
            variant="surface",
            color_scheme="amber",
            width="100%",
        ),
        rx.vstack(
            rx.text("New Administrator Password", size="2", font_weight="medium"),
            rx.input(
                placeholder="Enter new master password (min 6 characters)",
                type="password",
                value=AuthState.admin_setup_password,
                on_change=AuthState.set_admin_setup_password,
                width="100%",
                size="3",
            ),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("Confirm Administrator Password", size="2", font_weight="medium"),
            rx.input(
                placeholder="Confirm master password",
                type="password",
                value=AuthState.admin_setup_confirm,
                on_change=AuthState.set_admin_setup_confirm,
                width="100%",
                size="3",
            ),
            spacing="1",
            width="100%",
        ),
        rx.button(
            rx.hstack(
                rx.icon("key-round", size=18),
                rx.text("Save Admin Password & Sign In"),
                spacing="2",
                align="center",
            ),
            size="3",
            width="100%",
            color_scheme="amber",
            on_click=AuthState.setup_first_time_admin,
        ),
        rx.hstack(
            rx.button(
                "Cancel and return to Login",
                variant="ghost",
                size="2",
                color_scheme="gray",
                on_click=lambda: AuthState.set_auth_tab("login"),
            ),
            justify="center",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def auth_view() -> rx.Component:
    """Primary public landing page rendering the welcome hero and authentication card."""
    return rx.box(
        rx.vstack(
            # Top Branding Hero
            rx.vstack(
                rx.badge(
                    rx.hstack(
                        rx.icon("box", size=14),
                        rx.text("BoxVault v1.0", size="1", font_weight="bold"),
                        spacing="1",
                        align="center",
                    ),
                    variant="soft",
                    color_scheme="indigo",
                    radius="full",
                    size="2",
                ),
                rx.heading(
                    "Storage Boxes Management System",
                    size="8",
                    weight="bold",
                    text_align="center",
                ),
                rx.text(
                    "Keep track of physical storage boxes, organize items with precision, and locate any possession instantly with keyword search.",
                    size="3",
                    color_scheme="gray",
                    text_align="center",
                    max_width="560px",
                ),
                spacing="3",
                align="center",
                margin_bottom="5",
            ),

            # Authentication Card
            rx.card(
                rx.vstack(
                    admin_first_run_callout(),
                    auth_alerts(),

                    # Tab headers
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Sign In", value="login"),
                            rx.tabs.trigger("Register", value="register"),
                            rx.cond(
                                AuthState.admin_needs_first_time_setup,
                                rx.tabs.trigger("Admin Setup", value="admin_setup"),
                                rx.fragment(),
                            ),
                        ),
                        value=AuthState.auth_tab,
                        on_change=AuthState.set_auth_tab,
                        width="100%",
                    ),

                    # Form Content
                    rx.box(
                        rx.cond(
                            AuthState.auth_tab == "register",
                            register_form(),
                            rx.cond(
                                AuthState.auth_tab == "admin_setup",
                                admin_setup_form(),
                                login_form(),
                            ),
                        ),
                        width="100%",
                        padding_top="4",
                    ),
                    spacing="4",
                    width="100%",
                ),
                max_width="480px",
                width="100%",
                box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04)",
                padding="6",
                border_radius="16px",
            ),

            # Bottom Feature Pills
            rx.hstack(
                rx.badge("Physical Box Tracking", variant="outline", color_scheme="gray"),
                rx.badge("Instant Keyword Search", variant="outline", color_scheme="gray"),
                rx.badge("Admin User Controls", variant="outline", color_scheme="gray"),
                spacing="2",
                wrap="wrap",
                justify="center",
                margin_top="6",
            ),
            spacing="5",
            align="center",
            justify="center",
            min_height="85vh",
            padding_y="8",
        ),
        width="100%",
        background="radial-gradient(ellipse at top, var(--indigo-2), transparent 70%), var(--background)",
    )
