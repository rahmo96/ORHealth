"""Business logic layer for nutrition workflows."""

from __future__ import annotations

from datetime import date
import logging

from pydantic import ValidationError

from app.core.exceptions import ValidationAppError
from app.database.repository import NutritionRepository
from app.database.transaction import db_safe_operation
from app.models.schemas import DailySummary, FoodItem, MealBasketItem, MealLogCreate

LOGGER: logging.Logger = logging.getLogger(__name__)
DEFAULT_DAILY_GOAL: int = 1800
USER_DAILY_GOALS: dict[str, int] = {
    "רחמים": 1800,
    "אורלי": 1600,
}


class NutritionService:
    """Service layer that is independent from the Streamlit UI."""

    def __init__(self, repository: NutritionRepository) -> None:
        """Initialize service with repository dependency."""
        self._repository: NutritionRepository = repository

    def get_food_catalog(self) -> list[FoodItem]:
        """Return catalog for food selection."""
        return self._repository.fetch_food_catalog()

    @db_safe_operation
    def add_meal_log(
        self,
        *,
        user_name: str,
        food_name: str,
        calories_consumed: int,
        is_fail: bool,
    ) -> None:
        """Validate and store a meal log record."""
        try:
            meal = MealLogCreate(
                user_name=user_name,
                food_name=food_name,
                calories_consumed=calories_consumed,
                is_fail=is_fail,
            )
        except ValidationError as error:
            LOGGER.warning("Meal log validation failed: %s", error)
            raise ValidationAppError("Invalid meal log data.") from error
        self._repository.insert_daily_log(meal)

    @db_safe_operation
    def add_full_meal(self, *, user_name: str, items: list[MealBasketItem]) -> None:
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
                )
                for item in items
            ]
        except ValidationError as error:
            LOGGER.warning("Batch meal validation failed: %s", error)
            raise ValidationAppError("Invalid meal basket data.") from error
        self._repository.insert_daily_logs(validated)

    def get_daily_goal(self, user_name: str) -> int:
        """Return the configured daily calorie goal for a user."""
        return USER_DAILY_GOALS.get(user_name, DEFAULT_DAILY_GOAL)

    def get_daily_summary(self, *, user_name: str, target_date: date) -> DailySummary:
        """Calculate total and remaining calories for a user day."""
        logs = self._repository.fetch_daily_logs(user_name=user_name, target_date=target_date)
        total_calories: int = sum(item.calories_consumed for item in logs)
        fail_count: int = sum(1 for item in logs if item.is_fail)
        daily_goal: int = USER_DAILY_GOALS.get(user_name, DEFAULT_DAILY_GOAL)
        return DailySummary(
            total_calories=total_calories,
            fail_count=fail_count,
            daily_goal=daily_goal,
        )
