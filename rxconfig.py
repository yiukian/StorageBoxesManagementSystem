"""Reflex configuration file for BoxVault."""
import reflex as rx

config = rx.Config(
    app_name="box_vault",
    db_url="sqlite:///boxvault.db",
    telemetry_enabled=False,
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                has_background=True,
                accent_color="indigo",
                gray_color="slate",
                radius="large",
            )
        )
    ],
)
