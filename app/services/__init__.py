"""Services Package.

This package contains service layer implementations.
ML services are temporarily disabled due to dependency issues.

Usage:
    # ML services temporarily disabled
    pass
"""

import logging

# Services module initialization

logger = logging.get_logger(__name__)

# ML services temporarily disabled due to joblib/numpy dependency issues
# This will be re-enabled once dependencies are resolved

# Export public interface - temporarily empty
__all__ = []

logger.info("Services package loaded (ML services temporarily disabled)")
