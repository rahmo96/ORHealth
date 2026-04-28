"""Streamlit presentation layer for the ORHealth application."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
import logging
import os
from typing import Any

import streamlit as st
from streamlit.errors import StreamlitAPIException

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


def resolve_database_url() -> str | None:
    """Resolve database URL from environment or Streamlit secrets."""
    environment_url: str | None = os.getenv("DATABASE_URL")
    if environment_url:
        return environment_url

    connections: Any = st.secrets.get("connections")
    if connections and isinstance(connections, dict):
        postgres_config: Any = connections.get("postgresql")
        if postgres_config and isinstance(postgres_config, dict):
            secret_url: Any = postgres_config.get("url")
            if isinstance(secret_url, str) and secret_url.strip():
                return secret_url.strip()
    return None


def resolve_streamlit_sql_config() -> dict[str, Any]:
    """Resolve SQL connection config from Streamlit Cloud secrets TOML."""
    connections: Any = st.secrets.get("connections")
    if not isinstance(connections, Mapping):
        return {}

    postgres_config: Any = connections.get("postgresql")
    if not isinstance(postgres_config, Mapping):
        return {}

    return dict(postgres_config)


@st.cache_resource(show_spinner=False)
def get_service() -> NutritionService:
    """Build and cache the service object."""
    sql_config: dict[str, Any] = resolve_streamlit_sql_config()
    db_url: str | None = resolve_database_url()
    connection_kwargs: dict[str, Any] = dict(sql_config)
    if db_url:
        connection_kwargs["url"] = db_url
    if connection_kwargs.get("host", "").endswith(".supabase.co"):
        connection_kwargs.setdefault("sslmode", "require")
    try:
        connection: Any = st.connection("postgresql", type="sql", **connection_kwargs)
    except StreamlitAPIException as error:
        LOGGER.exception("Missing or invalid SQL connection configuration.")
        raise DatabaseAppError(
            "Missing SQL DB connection. Configure secrets.toml or DATABASE_URL."
        ) from error
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
    try:
        with st.spinner("טוען נתונים..."):
            render_dashboard(current_user)
    except DatabaseAppError as error:
        error_text: str = str(error)
        if "Cannot assign requested address" in error_text:
            st.error("Network route to DB failed (likely IPv6 route issue on host).")
            st.markdown(
                "Use your **Supabase Session Pooler** host in Streamlit secrets "
                "(not the direct `db.<project>.supabase.co` host)."
            )
        else:
            st.error("Missing or invalid SQL DB connection configuration.")
        st.markdown(
            "Configure Streamlit Cloud secrets with `[connections.postgresql]`."
            "\nRecommended: use Supabase pooler + `sslmode = \"require\"`."
        )
        st.code(
            '[connections.postgresql]\n'
            'url = "postgresql+psycopg2://postgres:YOUR_PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require"\n\n'
            '# or\n'
            '[connections.postgresql]\n'
            'dialect = "postgresql"\n'
            'host = "aws-0-REGION.pooler.supabase.com"\n'
            'port = 6543\n'
            'database = "postgres"\n'
            'username = "postgres"\n'
            'password = "YOUR_PASSWORD"\n'
            'sslmode = "require"',
            language="toml",
        )
        st.caption(f"Details: `{error_text[:240]}`")
        st.stop()


if __name__ == "__main__":
    main()