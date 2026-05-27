"""JS/CSS Webpack bundles for My Site."""

from invenio_assets.webpack import WebpackBundle

theme = WebpackBundle(
    __name__,
    "assets",
    entry={
        # Statistics page bundle (React + CSS)
        "statistics": "./pages/statistics/mount.js",
        "statistics-styles": "./pages/statistics/index.less",
        # Dashboard page bundle (React + CSS)
        "dashboard": "./pages/dashboard/mount.js",
        "dashboard-styles": "./pages/dashboard/index.less",
        # CMS administration page bundle (React + CSS)
        "cms": "./pages/administration/cms/mount.js",
        "cms-styles": "./pages/administration/cms/index.less",
        # Plain Language Summary detail page (React + CSS)
        "pls": "./pages/pls/mount.js",
        "pls-styles": "./pages/pls/index.less",
    },
    dependencies={
        "leaflet": "^1.9.4",
    },
)
