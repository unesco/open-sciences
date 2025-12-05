# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Create my_site branch for CMS migrations.

This is the initial migration that creates the my_site alembic branch.
All subsequent CMS migrations will depend on this branch.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "000000_my_site_branch"
down_revision = None
branch_labels = ("my_site",)
depends_on = "dbdbc1b19cf2"  # Depends on Invenio base transaction table


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
