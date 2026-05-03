"""Data-access layer for the `users` table."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from typing import Any, Generator, Sequence

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseAppError
from app.models.schemas import User

LOGGER: logging.Logger = logging.getLogger(__name__)


class UsersRepository:
    """Repository that encapsulates queries against the `users` table."""

    def __init__(self, connection: Any) -> None:
        """Initialize repository with a Streamlit SQL connection."""
        self._connection: Any = connection

    @contextmanager
    def session_scope(self) -> Generator[Any, None, None]:
        """Provide a transaction-safe session scope."""
        with self._connection.session as session:
            try:
                yield session
                session.commit()
            except SQLAlchemyError as error:
                session.rollback()
                LOGGER.exception("Users transaction failed.")
                raise DatabaseAppError(f"Users transaction failed: {error}") from error
            except Exception:
                session.rollback()
                LOGGER.exception("Unexpected users transaction error.")
                raise

    def list_users(self) -> list[User]:
        """Return all users ordered by display name."""
        query = text(
            """
            SELECT id,
                   display_name,
                   daily_calorie_goal,
                   (pin_hash IS NOT NULL) AS has_pin
            FROM users
            ORDER BY display_name ASC;
            """
        )
        try:
            with self.session_scope() as session:
                result = session.execute(query)
                rows: Sequence[Any] = result.fetchall()
            return [User.model_validate(dict(row._mapping)) for row in rows]
        except DatabaseAppError:
            raise
        except Exception as error:
            LOGGER.exception("Failed to list users.")
            raise DatabaseAppError("Failed to list users.") from error

    def get_by_display_name(self, display_name: str) -> User | None:
        """Return a user by display name, or None if missing."""
        query = text(
            """
            SELECT id,
                   display_name,
                   daily_calorie_goal,
                   (pin_hash IS NOT NULL) AS has_pin
            FROM users
            WHERE display_name = :display_name
            LIMIT 1;
            """
        )
        try:
            with self.session_scope() as session:
                result = session.execute(query, {"display_name": display_name})
                row: Any = result.fetchone()
            if row is None:
                return None
            return User.model_validate(dict(row._mapping))
        except DatabaseAppError:
            raise
        except Exception as error:
            LOGGER.exception("Failed to get user by display name.")
            raise DatabaseAppError("Failed to get user by display name.") from error

    def get_pin_hash(self, user_id: int) -> str | None:
        """Return the bcrypt PIN hash for a user, or None if not set."""
        query = text(
            """
            SELECT pin_hash
            FROM users
            WHERE id = :user_id
            LIMIT 1;
            """
        )
        try:
            with self.session_scope() as session:
                result = session.execute(query, {"user_id": user_id})
                row: Any = result.fetchone()
            if row is None:
                return None
            value: Any = row._mapping["pin_hash"]
            if value is None:
                return None
            return str(value)
        except DatabaseAppError:
            raise
        except Exception as error:
            LOGGER.exception("Failed to fetch PIN hash.")
            raise DatabaseAppError("Failed to fetch PIN hash.") from error

    def set_pin_hash(self, user_id: int, pin_hash: str) -> None:
        """Persist a new bcrypt PIN hash for a user."""
        query = text(
            """
            UPDATE users
            SET pin_hash = :pin_hash
            WHERE id = :user_id;
            """
        )
        with self.session_scope() as session:
            session.execute(query, {"user_id": user_id, "pin_hash": pin_hash})

    def update_daily_goal(self, user_id: int, goal: int) -> None:
        """Update a user's daily calorie goal."""
        query = text(
            """
            UPDATE users
            SET daily_calorie_goal = :goal
            WHERE id = :user_id;
            """
        )
        with self.session_scope() as session:
            session.execute(query, {"user_id": user_id, "goal": goal})
