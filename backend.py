import os
import time
import mysql.connector
from mysql.connector import pooling, errors as db_errors
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

class Database:
    """
    Database class using a connection pool to interact with a MySQL database.

    Improvements:
    - Robust `fetch` that supports CALL (stored procedures) by consuming extra
      result sets and returning the first result set as a list of dictionaries.
    - Retries once on transient InterfaceError ("MySQL Connection not available").
    - Careful resource cleanup to avoid leaking connections back to the pool
      in a broken state.
    """
    def __init__(self):
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="pharma_pool",
                pool_size=5,
                pool_reset_session=True,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "PharmaDB"),
                autocommit=True
            )
        except mysql.connector.Error as err:
            # If initialization fails, surface a clear message
            print(f"Error initializing database pool: {err}")
            raise

    def _get_connection(self):
        """Get a connection from the pool."""
        return self.pool.get_connection()

    def fetch(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT or CALL (stored procedure) and return rows from the
        first result set as a list of dictionaries.

        - Consumes any additional result sets (important when using CALL).
        - Retries once on InterfaceError to handle transient pool/connection issues.
        """
        attempts = 2
        last_exc = None

        for attempt in range(attempts):
            conn = None
            cursor = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())

                rows: List[Dict[str, Any]] = cursor.fetchall() if cursor.with_rows else []

                # Drain any additional result sets produced by CALL
                while cursor.nextset():
                    try:
                        if cursor.with_rows:
                            _ = cursor.fetchall()  # discard
                    except Exception:
                        # ignore errors while draining extra sets
                        pass

                return rows

            except db_errors.InterfaceError as e:
                # transient connection issue — close resources and retry once
                last_exc = e
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass

                if attempt + 1 < attempts:
                    time.sleep(0.2)
                    continue
                # re-raise after exhausting retries
                raise

            except Exception as e:
                # non-interface exceptions: ensure cleanup and re-raise
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass
                raise

            finally:
                # best-effort cleanup; if conn/cursor already closed this is fine
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass

        # if exhausted attempts, raise the last recorded exception
        if last_exc:
            raise last_exc

        return []

    def execute(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE or other non-select statement.
        Returns the cursor.rowcount.
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            # autocommit is enabled on pool creation; rowcount is available
            rowcount = cursor.rowcount
            return rowcount
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def execute_and_get_id(self, query: str, params: Optional[tuple] = None) -> Optional[int]:
        """
        Execute an INSERT and return the LAST_INSERT_ID() for that connection.
        Returns None if unable to obtain an ID.
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            # SELECT LAST_INSERT_ID() on the same connection
            cursor.execute("SELECT LAST_INSERT_ID()")
            row = cursor.fetchone()
            if row:
                # fetchone() returns a tuple, take the first element
                return int(row[0])
            return None
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass


# --- Singleton Instance ---
# Create a single, shared instance of the Database class for the entire application.
_db_instance = Database()

def get_db() -> Database:
    """Return the singleton database instance."""
    return _db_instance
