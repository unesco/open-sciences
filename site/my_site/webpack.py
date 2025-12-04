"""JS/CSS Webpack bundles for My Site."""

from invenio_assets.webpack import WebpackBundle

theme = WebpackBundle(
    __name__,
    "assets",
    entry={
        # Statistics dashboard bundle
        "my-site-statistics": "./js/statistics.js",
    },
)
