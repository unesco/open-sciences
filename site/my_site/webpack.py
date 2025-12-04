"""JS/CSS Webpack bundles for My Site."""

from invenio_assets.webpack import WebpackBundle

theme = WebpackBundle(
    __name__,
    "assets",
    entry={
        # Statistics page bundle (React + CSS)
        "statistics": "./js/statistics.js",
        "statistics-styles": "./less/statistics.less",
    },
)
