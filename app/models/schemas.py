"""Pydantic schemas for validated application data."""

from __future__ import annotations

from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_PATTERN: re.Pattern[str] = re.compile(r"^[\w\u0590-\u05FF\s-]{2,40}$")


class MealLogCreate(BaseModel):
    """Validated payload for creating a daily meal log."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_name: str = Field(min_length=2, max_length=40)
    food_name: str = Field(min_length=1, max_length=120)
    calories_consumed: int = Field(gt=0, le=10000)
    is_fail: bool = False

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, value: str) -> str:
        """Ensure username contains only allowed characters."""
        if not USERNAME_PATTERN.match(value):
            raise ValueError("Username includes invalid characters.")
        return value


class FoodItem(BaseModel):
    """Food catalog row returned from the database."""

    food_name: str
    default_calories: int = Field(gt=0)


class DailyLogRecord(BaseModel):
    """Daily log row returned from the database."""

    id: int
    user_name: str
    food_name: str
    calories_consumed: int = Field(gt=0)
    is_fail: bool
    created_at: datetime | None = None


class DailySummary(BaseModel):
    """Business-level daily summary for a user."""

    total_calories: int = Field(ge=0)
    fail_count: int = Field(ge=0)
    daily_goal: int = Field(gt=0)

    @property
    def remaining_calories(self) -> int:
        """Return remaining calories against daily goal."""
        return max(self.daily_goal - self.total_calories, 0)
