{
    "name": "Leas Save & Discard Buttons",
    "version": "18.0.0.0.0",
    "summary": "Save & Discard Buttons",
    "license": "AGPL-3",
    "category": "Tools",
    'author': "Leas",
    'website': "http://www.leasnow.com",
    "depends": ["web"],
    "data": [],
    # "images": ["static/description/main_screen.png"],
    "assets": {
        "web.assets_backend": [
            "leas_web_save_discard_but/static/src/scss/indicator_button.scss",
            "leas_web_save_discard_but/static/src/xml/template.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
