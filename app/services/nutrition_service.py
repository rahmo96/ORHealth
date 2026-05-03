"""Business logic layer for nutrition workflows."""

from __future__ import annotations

from datetime import date
import logging

from pydantic import ValidationError

from app.core.exceptions import ValidationAppError
from app.database.repository import NutritionRepository
from app.database.transaction import db_safe_operation
from app.database.users_repository import UsersRepository
from app.models.schemas import (
    DailyLogRecord,
    DailySummary,
    FoodItem,
    FoodMasterCreate,
    MealBasketItem,
    MealLogCreate,
    User,
)
from app.services.auth import hash_pin, is_valid_pin, verify_pin

LOGGER: logging.Logger = logging.getLogger(__name__)
DEFAULT_DAILY_GOAL: int = 1800


class NutritionService:
    """Service layer that is independent from the Streamlit UI."""

    def __init__(
        self,
        repository: NutritionRepository,
        users_repository: UsersRepository,
    ) -> None:
        """Initialize service with repository dependencies."""
        self._repository: NutritionRepository = repository
        self._users_repository: UsersRepository = users_repository

    def get_food_catalog(self) -> list[FoodItem]:
        """Return catalog for food selection."""
        return self._repository.fetch_food_catalog()

    @db_safe_operation
    def add_food_catalog_entry(self, *, food_name: str, default_calories: int) -> None:
        """Validate and insert a new row into foods_master."""
        try:
            payload: FoodMasterCreate = FoodMasterCreate(
                food_name=food_name,
                default_calories=default_calories,
            )
        except ValidationError as error:
            LOGGER.warning("Food catalog validation failed: %s", error)
            raise ValidationAppError("נתוני מאכל לא תקינים.") from error
        self._repository.insert_foods_master_row(
            food_name=payload.food_name,
            default_calories=payload.default_calories,
        )

    def list_users(self) -> list[User]:
        """Return all configured users."""
        return self._users_repository.list_users()

    def authenticate(self, *, display_name: str, pin: str) -> User:
        """Authenticate a user by display name + PIN, returning the user.

        Raises:
            ValidationAppError: if the user does not exist, the PIN is missing,
                or the PIN does not match.
        """
        if not is_valid_pin(pin):
            raise ValidationAppError("PIN must be 4-6 digits.")
        user: User | None = self._users_repository.get_by_display_name(display_name)
        if user is None:
            raise ValidationAppError("User not found.")
        if not user.has_pin:
            raise ValidationAppError("PIN is not set for this user.")
        stored_hash: str | None = self._users_repository.get_pin_hash(user.id)
        if stored_hash is None or not verify_pin(pin, stored_hash):
            raise ValidationAppError("Incorrect PIN.")
        return user

    @db_safe_operation
    def set_pin(self, *, user_id: int, pin: str) -> None:
        """Validate, hash and persist a new PIN for a user."""
        if not is_valid_pin(pin):
            raise ValidationAppError("PIN must be 4-6 digits.")
        new_hash: str = hash_pin(pin)
        self._users_repository.set_pin_hash(user_id, new_hash)

    @db_safe_operation
    def update_daily_goal(self, *, user_id: int, goal: int) -> None:
        """Validate and persist a new daily calorie goal for a user."""
        if not isinstance(goal, int) or goal <= 0:
            raise ValidationAppError("Daily goal must be a positive integer.")
        self._users_repository.update_daily_goal(user_id, goal)

    @db_safe_operation
    def add_meal_log(
        self,
        *,
        user_name: str,
        food_name: str,
        calories_consumed: int,
        is_fail: bool,
        meal_date: date,
        user_id: int | None = None,
    ) -> None:
        """Validate and store a meal log record."""
        try:
            meal = MealLogCreate(
                user_name=user_name,
                food_name=food_name,
                calories_consumed=calories_consumed,
                is_fail=is_fail,
                meal_date=meal_date,
                user_id=user_id,
            )
        except ValidationError as error:
            LOGGER.warning("Meal log validation failed: %s", error)
            raise ValidationAppError("Invalid meal log data.") from error
        self._repository.insert_daily_log(meal)

    @db_safe_operation
    def add_full_meal(
        self,
        *,
        user_name: str,
        items: list[MealBasketItem],
        user_id: int | None = None,
    ) -> None:
        """Validate and store a full meal basket in one transaction."""
        if not items:
            raise ValidationAppError("Meal basket is empty.")
        try:
            validated: list[MealLogCreate] = [
                MealLogCreate(
                    user_name=user_name,
                    food_name=item.food_name,
                    calories_consumed=item.calories_consumed,
                    is_fail=item.is_fail,
                    meal_date=item.meal_date,
                    user_id=user_id,
                )
                for item in items
            ]
        except ValidationError as error:
            LOGGER.warning("Batch meal validation failed: %s", error)
            raise ValidationAppError("Invalid meal basket data.") from error
        self._repository.insert_daily_logs(validated)

    def get_daily_goal(self, user_name: str) -> int:
        """Return the configured daily calorie goal for a user."""
        user: User | None = self._users_repository.get_by_display_name(user_name)
        if user is None:
            return DEFAULT_DAILY_GOAL
        return user.daily_calorie_goal

    def get_daily_logs(
        self,
        *,
        user_name: str,
        target_date: date,
        user_id: int | None = None,
    ) -> list[DailyLogRecord]:
        """Return all meal logs for a user on a selected day."""
        return self._repository.fetch_daily_logs(
            user_name=user_name, target_date=target_date, user_id=user_id
        )

    def get_journal_for_day(
        self,
        *,
        user_name: str,
        target_date: date,
        user_id: int | None = None,
    ) -> tuple[list[DailyLogRecord], DailySummary]:
        """Fetch logs once and derive the daily summary (single DB read)."""
        logs: list[DailyLogRecord] = self._repository.fetch_daily_logs(
            user_name=user_name, target_date=target_date, user_id=user_id
        )
        summary: DailySummary = self._summary_from_logs(logs=logs, user_name=user_name)
        return logs, summary

    def _summary_from_logs(self, *, logs: list[DailyLogRecord], user_name: str) -> DailySummary:
        """Build summary metrics from already-loaded log rows."""
        total_calories: int = sum(item.calories_consumed for item in logs)
        fail_count: int = sum(1 for item in logs if item.is_fail)
        daily_goal: int = self.get_daily_goal(user_name)
        return DailySummary(
            total_calories=total_calories,
            fail_count=fail_count,
            daily_goal=daily_goal,
        )

    def get_daily_summary(self, *, user_name: str, target_date: date) -> DailySummary:
        """Calculate total and remaining calories for a user day."""
        logs = self._repository.fetch_daily_logs(user_name=user_name, target_date=target_date)
        return self._summary_from_logs(logs=logs, user_name=user_name)
