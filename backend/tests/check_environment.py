# check_environment.py
# Confirms Python version, key packages, and ODBC drivers.

import sys
import importlib

print("Python version:", sys.version)

required_packages = [
    "flask",
    "flask_cors",
    "sqlalchemy",
    "pyodbc",
    "langchain_core",
    "langchain_google_genai",
    "sqlglot",
    "dotenv",
]

all_ok = True
for package_name in required_packages:
    try:
        importlib.import_module(package_name)
        print("OK      :", package_name)
    except ImportError as error:
        print("MISSING :", package_name, "->", error)
        all_ok = False

try:
    import pyodbc
    drivers = pyodbc.drivers()
    print("\nODBC drivers found:")
    for driver_name in drivers:
        print("  -", driver_name)
    sql_server_drivers = [d for d in drivers if "ODBC Driver" in d and "SQL Server" in d]
    if not sql_server_drivers:
        print("\nWARNING: No 'ODBC Driver 17/18 for SQL Server' found.")
        all_ok = False
except ImportError:
    all_ok = False

print("\nRESULT:", "Environment looks good." if all_ok else "Fix the items above first.")