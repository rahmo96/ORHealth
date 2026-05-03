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
        self._daily_logs_columns_cache: set[str] | None = None

    def _get_daily_logs_columns(self) -> set[str]:
        """Return the available columns for the daily_logs table (cached per repository)."""
        if self._daily_logs_columns_cache is not None:
            return self._daily_logs_columns_cache
        query = text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'daily_logs';
            """
        )
        with self.session_scope() as session:
            result = session.execute(query)
            rows: Sequence[Any] = result.fetchall()
        self._daily_logs_columns_cache = {str(row._mapping["column_name"]) for row in rows}
        return self._daily_logs_columns_cache

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
                raise DatabaseAppError(f"Database transaction failed: {error}") from error
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
        columns: set[str] = self._get_daily_logs_columns()
        has_meal_date: bool = "meal_date" in columns
        has_user_id: bool = "user_id" in columns and meal.user_id is not None

        column_list: list[str] = ["user_name", "food_name", "calories_consumed", "is_fail"]
        value_list: list[str] = [":user_name", ":food_name", ":calories_consumed", ":is_fail"]
        payload: dict[str, Any] = {
            "user_name": meal.user_name,
            "food_name": meal.food_name,
            "calories_consumed": meal.calories_consumed,
            "is_fail": meal.is_fail,
        }
        if has_meal_date:
            column_list.append("meal_date")
            value_list.append(":meal_date")
            payload["meal_date"] = meal.meal_date
        if has_user_id:
            column_list.append("user_id")
            value_list.append(":user_id")
            payload["user_id"] = meal.user_id

        query = text(
            f"INSERT INTO daily_logs ({', '.join(column_list)}) "
            f"VALUES ({', '.join(value_list)});"
        )
        with self.session_scope() as session:
            session.execute(query, payload)

    def insert_daily_logs(self, meals: list[MealLogCreate]) -> None:
        """Insert multiple meal log rows in one transaction."""
        if not meals:
            return
        columns: set[str] = self._get_daily_logs_columns()
        has_meal_date: bool = "meal_date" in columns
        has_user_id: bool = "user_id" in columns and all(meal.user_id is not None for meal in meals)

        column_list: list[str] = ["user_name", "food_name", "calories_consumed", "is_fail"]
        value_list: list[str] = [":user_name", ":food_name", ":calories_consumed", ":is_fail"]
        if has_meal_date:
            column_list.append("meal_date")
            value_list.append(":meal_date")
        if has_user_id:
            column_list.append("user_id")
            value_list.append(":user_id")

        query = text(
            f"INSERT INTO daily_logs ({', '.join(column_list)}) "
            f"VALUES ({', '.join(value_list)});"
        )
        payload: list[dict[str, Any]] = []
        for meal in meals:
            row: dict[str, Any] = {
                "user_name": meal.user_name,
                "food_name": meal.food_name,
                "calories_consumed": meal.calories_consumed,
                "is_fail": meal.is_fail,
            }
            if has_meal_date:
                row["meal_date"] = meal.meal_date
            if has_user_id:
                row["user_id"] = meal.user_id
            payload.append(row)
        with self.session_scope() as session:
            session.execute(query, payload)

    def fetch_daily_logs(
        self,
        user_name: str,
        target_date: date,
        user_id: int | None = None,
    ) -> list[DailyLogRecord]:
        """Fetch user logs for a specific date.

        When the `user_id` column exists and a value is provided, filtering is
        done by `user_id` (more correct under name changes). Otherwise it falls
        back to filtering by `user_name` for backward compatibility.
        """
        try:
            columns: set[str] = self._get_daily_logs_columns()
            has_created_at: bool = "created_at" in columns
            has_meal_date: bool = "meal_date" in columns
            has_user_id: bool = "user_id" in columns
            user_id_select: str = "user_id" if has_user_id else "NULL::bigint AS user_id"
            use_user_id_filter: bool = has_user_id and user_id is not None
            user_predicate: str = (
                "user_id = :user_id" if use_user_id_filter else "user_name = :user_name"
            )

            base_params: dict[str, Any] = {"target_date": target_date}
            if use_user_id_filter:
                base_params["user_id"] = user_id
            else:
                base_params["user_name"] = user_name

            if has_meal_date:
                query = text(
                    f"""
                    SELECT id, user_name, food_name, calories_consumed, is_fail,
                           NULL::timestamp AS created_at, meal_date, {user_id_select}
                    FROM daily_logs
                    WHERE {user_predicate}
                      AND meal_date = :target_date
                    ORDER BY id DESC;
                    """
                )
                params: dict[str, Any] = base_params
            elif has_created_at:
                query = text(
                    f"""
                    SELECT id, user_name, food_name, calories_consumed, is_fail,
                           created_at, NULL::date AS meal_date, {user_id_select}
                    FROM daily_logs
                    WHERE {user_predicate}
                      AND DATE(created_at) = :target_date
                    ORDER BY created_at DESC;
                    """
                )
                params = base_params
            else:
                LOGGER.warning(
                    "daily_logs.created_at is missing; using non-date-filtered fallback query."
                )
                fallback_params: dict[str, Any] = {}
                if use_user_id_filter:
                    fallback_params["user_id"] = user_id
                else:
                    fallback_params["user_name"] = user_name
                query = text(
                    f"""
                    SELECT id, user_name, food_name, calories_consumed, is_fail,
                           NULL::timestamp AS created_at, NULL::date AS meal_date, {user_id_select}
                    FROM daily_logs
                    WHERE {user_predicate}
                    ORDER BY id DESC;
                    """
                )
                params = fallback_params

            with self.session_scope() as session:
                result = session.execute(query, params)
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
