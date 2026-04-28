"""Streamlit presentation layer for the ORHealth application."""

from __future__ import annotations

from datetime import date
import logging
from typing import Any

import streamlit as st

from app.core.exceptions import AppError, DatabaseAppError, ValidationAppError
from app.core.logging_config import configure_logging
from app.database.repository import NutritionRepository
from app.models.schemas import DailySummary, FoodItem
from app.services.nutrition_service import NutritionService
from app.ui.styles import APP_CSS

st.set_page_config(page_title="ORHealth", page_icon="🍏", layout="centered")
configure_logging()
LOGGER: logging.Logger = logging.getLogger(__name__)
USER_CHOICES: tuple[str, str] = ("רחמים", "אורלי")


@st.cache_resource(show_spinner=False)
def get_service() -> NutritionService:
    """Build and cache the service object."""
    connection: Any = st.connection("postgresql", type="sql")
    repository = NutritionRepository(connection=connection)
    return NutritionService(repository=repository)


@st.cache_data(ttl=60, show_spinner=False)
def cached_food_catalog() -> list[FoodItem]:
    """Return cached food catalog."""
    return get_service().get_food_catalog()


@st.cache_data(ttl=30, show_spinner=False)
def cached_daily_summary(user_name: str, target_date: date) -> DailySummary:
    """Return cached daily summary."""
    return get_service().get_daily_summary(user_name=user_name, target_date=target_date)


def render_login() -> None:
    """Render login selection screen."""
    st.markdown('<div class="title">מי נכנס למערכת? 🍎</div>', unsafe_allow_html=True)
    first_col, second_col = st.columns(2)
    if first_col.button("🙋‍♂️ רחמים", use_container_width=True):
        st.session_state.logged_in_user = USER_CHOICES[0]
        st.rerun()
    if second_col.button("🙋‍♀️ אורלי", use_container_width=True):
        st.session_state.logged_in_user = USER_CHOICES[1]
        st.rerun()


def render_dashboard(user_name: str) -> None:
    """Render main dashboard and meal form."""
    st.markdown(f'<div class="title">היומן של {user_name}</div>', unsafe_allow_html=True)
    target_date: date = date.today()
    foods: list[FoodItem] = cached_food_catalog()
    food_options: list[str] = [item.food_name for item in foods]
    calories_by_food: dict[str, int] = {item.food_name: item.default_calories for item in foods}

    summary: DailySummary = cached_daily_summary(user_name=user_name, target_date=target_date)
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("סה\"כ קלוריות", summary.total_calories)
    metric_col2.metric("נותר להיום", summary.remaining_calories)
    metric_col3.metric("נפילות היום", summary.fail_count)

    with st.form("meal_form", clear_on_submit=True):
        selected_food: str = st.selectbox("בחר מאכל:", options=[""] + food_options)
        default_cals: int = calories_by_food.get(selected_food, 0)
        calories_input: int = int(st.number_input("קלוריות:", min_value=1, value=max(default_cals, 1)))
        is_fail: bool = st.toggle("נפילה? 😢")
        submitted: bool = st.form_submit_button("שמור ביומן ✅", use_container_width=True)

    if submitted:
        if not selected_food:
            st.toast("צריך לבחור מאכל לפני שמירה", icon="⚠️")
            return
        with st.status("שומר נתונים...", expanded=False) as status:
            try:
                get_service().add_meal_log(
                    user_name=user_name,
                    food_name=selected_food,
                    calories_consumed=calories_input,
                    is_fail=is_fail,
                )
                cached_daily_summary.clear()
                status.update(label="הנתון נשמר בהצלחה", state="complete")
                st.toast("נשמר בהצלחה", icon="✅")
                st.rerun()
            except ValidationAppError:
                LOGGER.warning("Validation error while saving meal.")
                status.update(label="קלט לא תקין", state="error")
                st.toast("הקלט לא תקין. בדוק את הנתונים.", icon="🚫")
            except DatabaseAppError:
                LOGGER.exception("Database error while saving meal.")
                status.update(label="שגיאת מסד נתונים", state="error")
                st.toast("שמירה נכשלה עקב שגיאת מסד נתונים.", icon="🔥")
            except AppError:
                LOGGER.exception("Application error while saving meal.")
                status.update(label="שגיאת יישום", state="error")
                st.toast("אירעה שגיאה בלתי צפויה.", icon="⚠️")
            except Exception:
                LOGGER.exception("Unexpected error while saving meal.")
                status.update(label="כשל בלתי צפוי", state="error")
                st.toast("שגיאה בלתי צפויה. נסה שוב.", icon="❌")


def main() -> None:
    """Run Streamlit presentation entry point."""
    st.markdown(APP_CSS, unsafe_allow_html=True)

    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None

    if st.session_state.logged_in_user is None:
        render_login()
        st.stop()

    current_user: str = str(st.session_state.logged_in_user)
    with st.spinner("טוען נתונים..."):
        render_dashboard(current_user)


if __name__ == "__main__":
    main()