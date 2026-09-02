import reflex as rx

config = rx.Config(
    app_name="domovod",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(accent_color="teal", radius="large", appearance="light")
        ),
    ]
)
