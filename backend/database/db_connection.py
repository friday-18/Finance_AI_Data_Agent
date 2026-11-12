# db_connection.py
# Purpose: create and share the SQLAlchemy engine for SQL Server, and
# provide a function to test the connection.
# Other files call get_engine(); they never build their own connections.

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config import config
from utils.logger import get_logger

logger = get_logger("db_connection")

# One engine for the whole application, created on first use.
_engine = None


def build_odbc_connection_string():
    """Build the ODBC connection string from config.py settings."""
    # Braces protect special characters (like ';') in the password.
    safe_password = "{" + config.DB_PASSWORD.replace("}", "}}") + "}"

    connection_string = (
        "DRIVER={" + config.DB_DRIVER + "};"
        "SERVER=" + config.DB_SERVER + ";"
        "DATABASE=" + config.DB_NAME + ";"
        "UID=" + config.DB_USER + ";"
        "PWD=" + safe_password + ";"
        "Encrypt=yes;"
        "TrustServerCertificate=" + config.DB_TRUST_SERVER_CERTIFICATE + ";"
    )
    return connection_string


def get_engine():
    """Return the shared SQLAlchemy engine, creating it on first use."""
    global _engine

    if _engine is not None:
        return _engine

    missing_settings = config.get_missing_database_settings()
    if len(missing_settings) > 0:
        message = "Missing database settings in .env: " + ", ".join(missing_settings)
        logger.error(message)
        raise ValueError(message)

    odbc_string = build_odbc_connection_string()
    sqlalchemy_url = "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_string)

    # pool_pre_ping checks a connection is alive before using it.
    # 'timeout' is the login timeout in seconds.
    _engine = create_engine(
        sqlalchemy_url,
        pool_pre_ping=True,
        connect_args={"timeout": 10},
    )
    logger.info("SQLAlchemy engine created for database " + config.DB_NAME)
    return _engine


def test_connection():
    """
    Try to connect and run a tiny query.
    Returns a dictionary and never raises, so it is safe for /api/health.
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            query = text("SELECT DB_NAME() AS database_name, SUSER_SNAME() AS login_name")
            row = connection.execute(query).fetchone()

        logger.info("Connection test succeeded")
        return {
            "connected": True,
            "database": row.database_name,
            "login": row.login_name,
            "message": "Connected to SQL Server successfully.",
        }

    except ValueError as error:
        return {"connected": False, "message": str(error)}

    except SQLAlchemyError as error:
        # Full technical error goes to the log file only.
        logger.error("Connection test failed: " + str(error))
        return {
            "connected": False,
            "message": "Could not connect to the database. Check the server, login and driver settings.",
        }