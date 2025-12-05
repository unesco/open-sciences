"""Flask extension for my_site customizations."""

from flask import current_app


class MySiteExt:
    """Extension to register my_site templates and resources."""

    def __init__(self, app=None):
        """Initialize extension."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize Flask application.

        This registers the my_site templates directory so that
        Jinja2 can find template overrides.
        """
        # Register the extension
        app.extensions["my-site"] = self

        # Add our templates directory to Jinja loader
        # This allows us to override InvenioRDM templates
        self._register_template_folder(app)

    def _register_template_folder(self, app):
        """Register my_site templates folder with Jinja."""
        from jinja2 import ChoiceLoader, FileSystemLoader
        import os

        # Get the path to my_site templates directory
        template_folder = os.path.join(os.path.dirname(__file__), "templates")

        # Add our template folder to the Jinja loader search path
        # This needs to be added BEFORE invenio_administration templates
        # so our overrides take precedence
        current_loader = app.jinja_loader

        if isinstance(current_loader, ChoiceLoader):
            # Insert our loader at the beginning of the list
            app.jinja_loader = ChoiceLoader(
                [FileSystemLoader(template_folder), *current_loader.loaders]
            )
        else:
            # Create a new ChoiceLoader with our folder first
            app.jinja_loader = ChoiceLoader(
                [FileSystemLoader(template_folder), current_loader]
            )
