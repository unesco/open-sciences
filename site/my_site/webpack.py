"""JS/CSS Webpack bundles for My Site."""

from invenio_assets.webpack import WebpackBundle

theme = WebpackBundle(
    __name__,
    "assets",
    entry={
        # Statistics page bundle (React + CSS)
        "statistics": "./statistics/index.js",
        "statistics-styles": "./statistics/index.less",
        # CMS administration page bundle (React + CSS)
        "cms": "./administration/cms/index.js",
        "cms-styles": "./administration/cms/index.less",
    },
)
