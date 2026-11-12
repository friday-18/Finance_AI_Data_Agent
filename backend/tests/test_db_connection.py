# test_db_connection.py
# Phase 2 test. Run from the project root:
#   python backend\tests\test_db_connection.py

import os
import sys

TESTS_FOLDER = os.path.dirname(os.path.abspath(__file__))
BACKEND_FOLDER = os.path.dirname(TESTS_FOLDER)
sys.path.insert(0, BACKEND_FOLDER)

from database import db_connection  # noqa: E402

print("Testing SQL Server connection...")
result = db_connection.test_connection()

if result["connected"]:
    print("SUCCESS:", result["message"])
    print("  Database:", result["database"])
    print("  Logged in as:", result["login"])
else:
    print("FAILED:", result["message"])
    print("See backend\\logs\\app.log for technical details.")