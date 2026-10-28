"""Box card component representing physical storage boxes and their contained items."""
import reflex as rx
from box_vault.models import ItemView, BoxView
from box_vault.state import InventoryState


def render_item_row(item: ItemView) -> rx.Component:
    """Renders an individual item row inside a storage box with delete action."""
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
        rx.icon_button(
            rx.icon("trash-2", size=13),
            size="1",
            variant="ghost",
            color_scheme="red",
            cursor="pointer",
            title="Delete Item",
            on_click=lambda: InventoryState.delete_item(item.id),
        ),
        align="center",
        spacing="2",
        padding_y="1",
        padding_x="2",
        border_radius="6px",
        background="var(--gray-2)",
        width="100%",
    )


def render_box_card(box: BoxView) -> rx.Component:
    """Renders a responsive card representing a physical storage box."""
    return rx.card(
        rx.vstack(
            # Top Header: Box Title, Badges, and Delete Box Button
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.icon("box", size=18, color="var(--indigo-9)"),
                        padding="1.5",
                        background="var(--indigo-3)",
                        border_radius="6px",
                    ),
                    rx.heading(
                        box.label_name,
                        size="4",
                        weight="bold",
                        line_clamp=1,
                    ),
                    spacing="2",
                    align="center",
                    flex="1",
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=16),
                    size="2",
                    variant="ghost",
                    color_scheme="red",
                    cursor="pointer",
                    title="Delete entire Box",
                    on_click=lambda: InventoryState.delete_box(box.id),
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

            # Inline "Add Item" Form Combo
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
            spacing="3",
            width="100%",
        ),
        variant="surface",
        border_radius="12px",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
        width="100%",
    )
