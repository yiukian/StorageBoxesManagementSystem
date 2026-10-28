"""BoxVault - Reflex application main entrypoint."""
import reflex as rx
from box_vault.pages.index import index
from box_vault.state import rxState

# Instantiate Reflex App
app = rx.App()

# Register root page and bind on_load initialization handler
app.add_page(
    index,
    route="/",
    title="BoxVault - Storage Boxes Management System",
    on_load=rxState.check_and_init,
)
