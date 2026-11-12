# schema_reader.py
# Purpose: discover the structure of the SQL Server database automatically.
#
# It finds:  schemas, tables, columns, data types, primary keys,
#            foreign keys and the relationships between tables.
#
# It contains NO hardcoded table definitions. If you add a new table to
# the database, it will appear here after the cache refreshes.
#
# Who uses this file:
#   - sql_agent.py        -> get_schema_text_for_prompt()  (Phase 5)
#   - query_validator.py  -> get_table_names()             (Phase 5)

import time

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from config import config
from database import db_connection
from utils.logger import get_logger

# 'inspect' is SQLAlchemy's tool for reading database metadata.
# 'time' lets us remember WHEN we read the schema, for caching.

logger = get_logger("schema_reader")

# ---------------- Cache (kept in memory) ----------------
# _cached_schema holds the schema dictionary after the first read.
# _cached_at holds the time (in seconds) when it was read.
_cached_schema = None
_cached_at = 0

# Schemas that belong to SQL Server itself. We never show these to the AI.
SYSTEM_SCHEMA_NAMES = ["sys", "INFORMATION_SCHEMA", "guest"]


def is_system_schema(schema_name):
    """Return True if this schema is internal to SQL Server."""
    if schema_name in SYSTEM_SCHEMA_NAMES:
        return True
    # Built-in database role schemas are named db_owner, db_datareader, ...
    if schema_name.startswith("db_"):
        return True
    return False


def clean_data_type(raw_type):
    """
    Turn 'VARCHAR(50) COLLATE "SQL_Latin1_General_CP1_CI_AS"' into 'VARCHAR(50)'.
    The collation is a sorting rule that the AI does not need to know about.
    """
    type_text = str(raw_type)
    collate_position = type_text.find(" COLLATE")
    if collate_position != -1:
        type_text = type_text[:collate_position]
    return type_text


def read_columns(inspector, table_name, schema_name):
    """Return a list of column descriptions for one table."""
    column_list = []
    raw_columns = inspector.get_columns(table_name, schema=schema_name)

    for raw_column in raw_columns:
        column_info = {
            "name": raw_column["name"],
            "data_type": clean_data_type(raw_column["type"]),
            "nullable": bool(raw_column["nullable"]),
        }
        column_list.append(column_info)

    return column_list


def read_primary_key(inspector, table_name, schema_name):
    """Return the list of primary key column names (empty if none)."""
    primary_key_info = inspector.get_pk_constraint(table_name, schema=schema_name)
    key_columns = primary_key_info.get("constrained_columns")
    if key_columns is None:
        return []
    return list(key_columns)


def read_foreign_keys(inspector, table_name, schema_name):
    """Return a list of foreign keys for one table."""
    foreign_key_list = []
    raw_foreign_keys = inspector.get_foreign_keys(table_name, schema=schema_name)

    for raw_key in raw_foreign_keys:
        # If the referenced table is in the default schema, SQLAlchemy may
        # return None. In SQL Server the default schema is 'dbo'.
        referred_schema = raw_key.get("referred_schema")
        if referred_schema is None:
            referred_schema = "dbo"

        foreign_key_info = {
            "name": raw_key.get("name"),
            "columns": list(raw_key["constrained_columns"]),
            "referred_schema": referred_schema,
            "referred_table": raw_key["referred_table"],
            "referred_columns": list(raw_key["referred_columns"]),
        }
        foreign_key_list.append(foreign_key_info)

    return foreign_key_list


def read_schema_from_database():
    """
    Connect to SQL Server and read the full schema.
    This is the slow part, so get_schema() caches the result.

    Returns a dictionary like:
    {
      "database": "FinanceDB",
      "tables": [
        {
          "schema": "dbo",
          "name": "Customers",
          "full_name": "dbo.Customers",
          "columns": [{"name": "CustomerID", "data_type": "INTEGER", "nullable": False}, ...],
          "primary_key": ["CustomerID"],
          "foreign_keys": [ ... ]
        },
        ...
      ]
    }
    """
    engine = db_connection.get_engine()
    inspector = inspect(engine)

    table_list = []

    all_schema_names = inspector.get_schema_names()
    for schema_name in all_schema_names:
        if is_system_schema(schema_name):
            continue

        table_names = inspector.get_table_names(schema=schema_name)
        for table_name in table_names:
            table_info = {
                "schema": schema_name,
                "name": table_name,
                "full_name": schema_name + "." + table_name,
                "columns": read_columns(inspector, table_name, schema_name),
                "primary_key": read_primary_key(inspector, table_name, schema_name),
                "foreign_keys": read_foreign_keys(inspector, table_name, schema_name),
            }
            table_list.append(table_info)

    schema_result = {
        "database": config.DB_NAME,
        "tables": table_list,
    }
    logger.info("Schema read from database: " + str(len(table_list)) + " tables found")
    return schema_result


def cache_is_still_valid():
    """Return True if we have a cached schema that is not too old."""
    if _cached_schema is None:
        return False

    age_in_seconds = time.time() - _cached_at
    maximum_age_in_seconds = config.SCHEMA_CACHE_MINUTES * 60
    return age_in_seconds < maximum_age_in_seconds


def get_schema(force_refresh=False):
    """
    Return the schema dictionary, using the cache when possible.
    Pass force_refresh=True to ignore the cache and read again.
    """
    global _cached_schema
    global _cached_at

    if force_refresh is False and cache_is_still_valid():
        return _cached_schema

    try:
        _cached_schema = read_schema_from_database()
        _cached_at = time.time()
        return _cached_schema

    except SQLAlchemyError as error:
        logger.error("Could not read schema: " + str(error))
        # If we still have an older cached copy, it is better than nothing.
        if _cached_schema is not None:
            logger.warning("Using the older cached schema instead.")
            return _cached_schema
        raise


def refresh_schema():
    """Force a fresh read. Call this after the database structure changes."""
    logger.info("Schema refresh requested")
    return get_schema(force_refresh=True)


def get_table_names():
    """Return a list of full table names such as ['dbo.Customers', ...]."""
    schema = get_schema()
    names = []
    for table_info in schema["tables"]:
        names.append(table_info["full_name"])
    return names


def get_relationships():
    """
    Return the foreign key relationships as readable text lines, like:
      dbo.Accounts.CustomerID -> dbo.Customers.CustomerID
    """
    schema = get_schema()
    relationship_lines = []

    for table_info in schema["tables"]:
        for foreign_key in table_info["foreign_keys"]:
            for position in range(len(foreign_key["columns"])):
                from_column = foreign_key["columns"][position]
                to_column = foreign_key["referred_columns"][position]
                line = (
                    table_info["full_name"] + "." + from_column
                    + " -> "
                    + foreign_key["referred_schema"] + "."
                    + foreign_key["referred_table"] + "." + to_column
                )
                relationship_lines.append(line)

    return relationship_lines


def get_schema_text_for_prompt():
    """
    Turn the schema into plain text that can be placed inside the Gemini
    prompt. This is how the AI 'learns' your database structure.
    """
    schema = get_schema()
    text_lines = []

    text_lines.append("Database: " + schema["database"])
    text_lines.append("")

    for table_info in schema["tables"]:
        text_lines.append("TABLE " + table_info["full_name"])

        for column in table_info["columns"]:
            if column["nullable"]:
                null_text = "NULL"
            else:
                null_text = "NOT NULL"
            text_lines.append(
                "  - " + column["name"] + " (" + column["data_type"] + ", " + null_text + ")"
            )

        if len(table_info["primary_key"]) > 0:
            text_lines.append("  PRIMARY KEY: " + ", ".join(table_info["primary_key"]))

        for foreign_key in table_info["foreign_keys"]:
            text_lines.append(
                "  FOREIGN KEY: " + ", ".join(foreign_key["columns"])
                + " references " + foreign_key["referred_schema"] + "."
                + foreign_key["referred_table"]
                + "(" + ", ".join(foreign_key["referred_columns"]) + ")"
            )

        text_lines.append("")

    relationship_lines = get_relationships()
    if len(relationship_lines) > 0:
        text_lines.append("RELATIONSHIPS (join these columns):")
        for line in relationship_lines:
            text_lines.append("  " + line)

    return "\n".join(text_lines)