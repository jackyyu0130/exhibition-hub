"""Core package for the Taiwan Exhibition Journal data pipeline.

This package contains reusable collectors, normalization rules, validation,
deduplication, publishing, and monitoring components.

The existing ``scripts/scraper.py`` remains the production entry point while
the updater is migrated incrementally into this package.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
