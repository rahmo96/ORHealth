"""Pydantic schemas for validated application data."""

from __future__ import annotations

from datetime import date, datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# תבנית לאימות שם המשתמש - תומכת בעברית, אנגלית ומספרים
USERNAME_PATTERN: re.Pattern[str] = re.compile(r"^[\w\u0590-\u05FF\s-]{2,40}$")

class MealLogCreate(BaseModel):
    """נתונים לאימות עבור יצירת רשומה חדשה ביומן."""
    model_config = ConfigDict(str_strip_whitespace=True)

    user_name: str = Field(min_length=2, max_length=40)
    food_name: str = Field(min_length=1, max_length=120)
    calories_consumed: int = Field(gt=0, le=10000)
    is_fail: bool = False
    meal_date: date | None = None
    user_id: int | None = Field(default=None, gt=0)

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, value: str) -> str:
        """וידוא ששם המשתמש מכיל רק תווים מורשים."""
        if not USERNAME_PATTERN.match(value):
            raise ValueError("Username includes invalid characters.")
        return value


class User(BaseModel):
    """פרופיל משתמש כפי שנשמר בטבלת users."""
    id: int = Field(gt=0)
    display_name: str = Field(min_length=2, max_length=40)
    daily_calorie_goal: int = Field(gt=0)
    has_pin: bool = False

class FoodItem(BaseModel):
    """שורת קטלוג מזון כפי שחוזרת מהדאטה-בייס."""
    food_name: str
    default_calories: int = Field(gt=0)

class MealBasketItem(BaseModel):
    """פריט בודד המאוחסן בסל הארוחות הזמני בממשק המשתמש."""
    food_name: str = Field(min_length=1, max_length=120)
    calories_consumed: int = Field(gt=0, le=10000)
    is_fail: bool = False
    meal_date: date

class DailyLogRecord(BaseModel):
    """שורת לוג יומית כפי שחוזרת מהדאטה-בייס."""
    id: int
    user_name: str
    food_name: str
    calories_consumed: int = Field(gt=0)
    is_fail: bool
    created_at: datetime | None = None
    meal_date: date | None = None
    user_id: int | None = None

class DailySummary(BaseModel):
    """סיכום יומי עבור המשתמש."""
    total_calories: int = Field(ge=0)
    fail_count: int = Field(ge=0)
    daily_goal: int = Field(gt=0)

    @property
    def remaining_calories(self) -> int:
        """חישוב יתרת הקלוריות אל מול היעד היומי."""
        return max(self.daily_goal - self.total_calories, 0)