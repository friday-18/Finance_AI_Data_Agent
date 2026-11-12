# test_schema_reader.py
# Phase 3 test. Run from the project root:
#   python backend\tests\test_schema_reader.py

import os
import sys
import time

TESTS_FOLDER = os.path.dirname(os.path.abspath(__file__))
BACKEND_FOLDER = os.path.dirname(TESTS_FOLDER)
sys.path.insert(0, BACKEND_FOLDER)

from database import schema_reader  # noqa: E402

print("=== Test 1: read the schema from SQL Server ===")
start_time = time.time()
schema = schema_reader.get_schema()
first_read_seconds = time.time() - start_time
print("Tables found:", len(schema["tables"]))
print("Time taken: " + str(round(first_read_seconds, 3)) + " seconds")

print("\n=== Test 2: table names ===")
for table_name in schema_reader.get_table_names():
    print("  -", table_name)

print("\n=== Test 3: relationships ===")
relationships = schema_reader.get_relationships()
if len(relationships) == 0:
    print("  (no foreign keys found)")
for line in relationships:
    print("  ", line)

print("\n=== Test 4: cache (second call should be much faster) ===")
start_time = time.time()
schema_again = schema_reader.get_schema()
second_read_seconds = time.time() - start_time
print("Time taken: " + str(round(second_read_seconds, 5)) + " seconds")
print("Same cached object returned:", schema_again is schema)

print("\n=== Test 5: forced refresh ===")
refreshed_schema = schema_reader.refresh_schema()
print("Tables after refresh:", len(refreshed_schema["tables"]))

print("\n=== Test 6: text that will be given to Gemini ===")
print(schema_reader.get_schema_text_for_prompt())