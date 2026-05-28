# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Fixtures module for loading initial data."""

from .cms import get_all_fixtures, get_fixture

__all__ = (
    "get_fixture",
    "get_all_fixtures",
)
