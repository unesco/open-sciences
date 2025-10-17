"""JS/CSS Webpack bundles for My Site."""

from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                # Statistics dashboard bundle
                "my-site-statistics": "./js/my_site/statistics.js",
            },
        ),
    },
)
