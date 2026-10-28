"""Reflex configuration file for BoxVault."""
import reflex as rx

config = rx.Config(
    app_name="box_vault",
    db_url="sqlite:///boxvault.db",
    telemetry_enabled=False,
)
