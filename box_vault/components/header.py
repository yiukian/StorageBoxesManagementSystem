"""Sticky top header bar with live search input and creation trigger."""
import reflex as rx
from box_vault.state import InventoryState, rxState


def header() -> rx.Component:
    """Renders the sticky global search and action header."""
    return rx.box(
        rx.hstack(
            # Global Live Search Bar
            rx.hstack(
                rx.icon("search", size=18, color="var(--gray-9)"),
                rx.input(
                    placeholder="Search boxes, storage locations, or items...",
                    value=InventoryState.search_query,
                    on_change=InventoryState.set_search_query,
                    variant="surface",
                    size="3",
                    width="100%",
                ),
                rx.cond(
                    InventoryState.search_query != "",
                    rx.icon_button(
                        rx.icon("x", size=16),
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        on_click=lambda: InventoryState.set_search_query(""),
                    ),
                    rx.fragment(),
                ),
                align="center",
                spacing="2",
                flex="1",
                max_width="650px",
            ),

            rx.spacer(),

            # Action Area
            rx.cond(
                rxState.active_tab == "inventory",
                rx.button(
                    rx.hstack(
                        rx.icon("plus", size=18),
                        rx.text("New Box"),
                        spacing="2",
                        align="center",
                    ),
                    color_scheme="indigo",
                    size="3",
                    on_click=InventoryState.open_create_box,
                ),
                rx.fragment(),
            ),
            align="center",
            width="100%",
        ),
        position="sticky",
        top="0",
        z_index="50",
        padding_y="3",
        padding_x="6",
        background="var(--background)",
        border_bottom="1px solid var(--gray-4)",
        width="100%",
    )
