"""BoxVault - Reflex application main entrypoint."""
import reflex as rx
from box_vault.pages.index import index
from box_vault.state import rxState

# Instantiate Reflex App configured with Radix theme
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        accent_color="indigo",
        gray_color="slate",
        radius="large",
    )
)

# Register root page and bind on_load initialization handler
app.add_page(
    index,
    route="/",
    title="BoxVault - Storage Boxes Management System",
    on_load=rxState.check_and_init,
)
