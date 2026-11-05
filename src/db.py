# DB module

"""
Database connection handling.
Replace with actual implementation.
"""

import os

# placeholder
def get_connection_string() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///:memory:")
