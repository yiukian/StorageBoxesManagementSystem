"""Sticky top header bar with live search input, archive view toggle, and creation trigger."""
import reflex as rx
from box_vault.state import InventoryState, rxState


def header() -> rx.Component:
    """Renders the sticky global search, archive toggle, and action header."""
    return rx.box(
        rx.hstack(
            # Global Live Search Bar
            rx.hstack(
                rx.icon("search", size=18, color="var(--gray-9)"),
                rx.input(
                    placeholder="Search boxes, locations, owners, or items...",
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
                max_width="520px",
            ),

            rx.spacer(),

            # Archive View Toggle Buttons (Active vs. Archived)
            rx.cond(
                rxState.active_tab == "inventory",
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.icon("boxes", size=15),
                            rx.text("Active Boxes"),
                            spacing="1",
                            align="center",
                        ),
                        size="2",
                        variant=rx.cond(~InventoryState.show_archived, "solid", "surface"),
                        color_scheme=rx.cond(~InventoryState.show_archived, "indigo", "gray"),
                        cursor="pointer",
                        on_click=lambda: InventoryState.set_show_archived(False),
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("archive", size=15),
                            rx.text("Archived Boxes"),
                            spacing="1",
                            align="center",
                        ),
                        size="2",
                        variant=rx.cond(InventoryState.show_archived, "solid", "surface"),
                        color_scheme=rx.cond(InventoryState.show_archived, "amber", "gray"),
                        cursor="pointer",
                        on_click=lambda: InventoryState.set_show_archived(True),
                    ),
                    spacing="1",
                    align="center",
                    padding_right="2",
                ),
                rx.fragment(),
            ),

            # Action Area: New Box Button
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
