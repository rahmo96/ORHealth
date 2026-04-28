"""Data-access layer using SQLAlchemy text queries."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
import logging
from typing import Any, Generator, Sequence

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseAppError
from app.models.schemas import DailyLogRecord, FoodItem, MealLogCreate

LOGGER: logging.Logger = logging.getLogger(__name__)


class NutritionRepository:
    """Repository that encapsulates all database queries."""

    def __init__(self, connection: Any) -> None:
        """Initialize repository with Streamlit SQL connection.

        Args:
            connection: Streamlit SQL connection object from `st.connection`.
        """
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
                LOGGER.exception("Database transaction failed.")
                raise DatabaseAppError("Database transaction failed.") from error
            except Exception:
                session.rollback()
                LOGGER.exception("Unexpected transaction error.")
                raise

    def fetch_food_catalog(self) -> list[FoodItem]:
        """Return all foods with default calories."""
        query = text(
            """
            SELECT food_name, default_calories
            FROM foods_master
            ORDER BY food_name ASC;
            """
        )
        try:
            with self.session_scope() as session:
                result = session.execute(query)
                rows: Sequence[Any] = result.fetchall()
            return [FoodItem.model_validate(dict(row._mapping)) for row in rows]
        except DatabaseAppError:
            raise
        except Exception as error:
            LOGGER.exception("Failed to fetch food catalog.")
            raise DatabaseAppError("Failed to fetch food catalog.") from error

    def insert_daily_log(self, meal: MealLogCreate) -> None:
        """Insert one meal log row."""
        query = text(
            """
            INSERT INTO daily_logs (user_name, food_name, calories_consumed, is_fail)
            VALUES (:user_name, :food_name, :calories_consumed, :is_fail);
            """
        )
        with self.session_scope() as session:
            session.execute(
                query,
                {
                    "user_name": meal.user_name,
                    "food_name": meal.food_name,
                    "calories_consumed": meal.calories_consumed,
                    "is_fail": meal.is_fail,
                },
            )

    def fetch_daily_logs(self, user_name: str, target_date: date) -> list[DailyLogRecord]:
        """Fetch user logs for a specific date."""
        query = text(
            """
            SELECT id, user_name, food_name, calories_consumed, is_fail, created_at
            FROM daily_logs
            WHERE user_name = :user_name
              AND DATE(created_at) = :target_date
            ORDER BY created_at DESC;
            """
        )
        try:
            with self.session_scope() as session:
                result = session.execute(
                    query,
                    {"user_name": user_name, "target_date": target_date},
                )
                rows: Sequence[Any] = result.fetchall()
            return [
                DailyLogRecord.model_validate(dict(row._mapping))
                for row in rows
            ]
        except DatabaseAppError:
            raise
        except Exception as error:
            LOGGER.exception("Failed to fetch daily logs.")
            raise DatabaseAppError("Failed to fetch daily logs.") from error
