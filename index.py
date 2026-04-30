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
from app.models.schemas import DailyLogRecord, DailySummary, FoodItem, MealBasketItem
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
    connect_args: dict[str, Any] = {}
    sslmode_value: Any = connection_kwargs.pop("sslmode", None)
    if isinstance(sslmode_value, str) and sslmode_value.strip():
        connect_args["sslmode"] = sslmode_value.strip()
    if connection_kwargs.get("host", "").endswith(".supabase.co") and "sslmode" not in connect_args:
        connect_args["sslmode"] = "require"
    if connect_args:
        connection_kwargs["connect_args"] = connect_args
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
def cached_food_catalog() -> list[dict[str, Any]]:
    """Return cached food catalog as serializable dictionaries."""
    return [item.model_dump() for item in get_service().get_food_catalog()]


@st.cache_data(ttl=30, show_spinner=False)
def cached_daily_summary(user_name: str, target_date: date) -> dict[str, Any]:
    """Return cached daily summary as a serializable dictionary."""
    return get_service().get_daily_summary(user_name=user_name, target_date=target_date).model_dump()


@st.cache_data(ttl=30, show_spinner=False)
def cached_daily_logs(user_name: str, target_date: date) -> list[dict[str, Any]]:
    """Return cached daily logs as serializable dictionaries."""
    records: list[DailyLogRecord] = get_service().get_daily_logs(
        user_name=user_name,
        target_date=target_date,
    )
    return [record.model_dump(mode="json") for record in records]


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
    """Render meal journal with basket and batch save."""
    st.markdown(f'<div class="title">היומן של {user_name}</div>', unsafe_allow_html=True)
    target_date: date = st.date_input("בחר יום ביומן", value=date.today(), format="YYYY-MM-DD")
    foods: list[FoodItem] = [
        FoodItem.model_validate(item) for item in cached_food_catalog()
    ]
    food_options: list[str] = [item.food_name for item in foods]
    calories_by_food: dict[str, int] = {item.food_name: item.default_calories for item in foods}

    summary: DailySummary = DailySummary.model_validate(
        cached_daily_summary(user_name=user_name, target_date=target_date)
    )
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-icon" style="color:#E76F51;">🔥</div>
            <div class="summary-title">סה"כ קלוריות</div>
            <div class="summary-value">{summary.total_calories}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metric_col2.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-icon" style="color:#6D4C82;">💜</div>
            <div class="summary-title">נותר להיום</div>
            <div class="summary-value">{summary.remaining_calories}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metric_col3.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-icon" style="color:#C7B67B;">☹️</div>
            <div class="summary-title">נפילות היום</div>
            <div class="summary-value">{summary.fail_count}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="entry-shell">', unsafe_allow_html=True)
    with st.form("meal_form", clear_on_submit=True):
        selected_food: str = st.selectbox("🍴 בחר מאכל", options=[""] + food_options)
        default_cals: int = calories_by_food.get(selected_food, 0)
        st.number_input(
            "כמות קלוריות (נעול לפי מסד נתונים)",
            min_value=1,
            value=max(default_cals, 1),
            disabled=True,
        )
        is_fail: bool = st.toggle("?נפילה 😳")
        submitted: bool = st.form_submit_button("＋ הוסף לארוחה", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not selected_food:
            st.toast("צריך לבחור מאכל לפני שמירה", icon="⚠️")
            return
        basket_item = MealBasketItem(
            food_name=selected_food,
            calories_consumed=default_cals,
            is_fail=is_fail,
            meal_date=target_date,
        )
        st.session_state.meal_basket.append(basket_item.model_dump())
        st.toast("הפריט נוסף לסל הארוחה", icon="🧺")
        st.rerun()

    basket_data: list[dict[str, Any]] = st.session_state.meal_basket
    basket_items_all: list[MealBasketItem] = [MealBasketItem.model_validate(item) for item in basket_data]
    basket_items_for_date: list[MealBasketItem] = [
        item for item in basket_items_all if item.meal_date == target_date
    ]
    st.subheader(f"סל ארוחה לתאריך {target_date.isoformat()}")
    if basket_items_for_date:
        basket_items: list[MealBasketItem] = basket_items_for_date
        basket_total: int = sum(item.calories_consumed for item in basket_items)
        st.caption(f"פריטים בסל: {len(basket_items)} | סה\"כ קלוריות: {basket_total}")
        st.dataframe(
            {
                "מאכל": [item.food_name for item in basket_items],
                "קלוריות": [item.calories_consumed for item in basket_items],
                "נפילה": ["כן" if item.is_fail else "לא" for item in basket_items],
            },
            use_container_width=True,
            hide_index=True,
        )
        control_col1, control_col2 = st.columns(2)
        if control_col1.button("שמור ארוחה מלאה ✅", use_container_width=True):
            with st.status("שומר את כל הסל...", expanded=False) as status:
                try:
                    get_service().add_full_meal(user_name=user_name, items=basket_items)
                    st.session_state.meal_basket = [
                        item.model_dump()
                        for item in basket_items_all
                        if item.meal_date != target_date
                    ]
                    cached_daily_summary.clear()
                    cached_daily_logs.clear()
                    status.update(label="הארוחה נשמרה בהצלחה", state="complete")
                    st.toast("כל הפריטים נשמרו בהצלחה", icon="🎉")
                    st.rerun()
                except ValidationAppError:
                    LOGGER.warning("Validation error while saving full meal.")
                    status.update(label="קלט לא תקין", state="error")
                    st.toast("הקלט לא תקין. בדוק את סל הארוחה.", icon="🚫")
                except DatabaseAppError:
                    LOGGER.exception("Database error while saving full meal.")
                    status.update(label="שגיאת מסד נתונים", state="error")
                    st.toast("שמירה נכשלה עקב שגיאת מסד נתונים.", icon="🔥")
                except AppError:
                    LOGGER.exception("Application error while saving full meal.")
                    status.update(label="שגיאת יישום", state="error")
                    st.toast("אירעה שגיאה בלתי צפויה.", icon="⚠️")
                except Exception:
                    LOGGER.exception("Unexpected error while saving full meal.")
                    status.update(label="כשל בלתי צפוי", state="error")
                    st.toast("שגיאה בלתי צפויה. נסה שוב.", icon="❌")
        if control_col2.button("נקה סל 🗑️", use_container_width=True):
            st.session_state.meal_basket = [
                item.model_dump()
                for item in basket_items_all
                if item.meal_date != target_date
            ]
            st.toast("סל הארוחה נוקה", icon="🧹")
            st.rerun()
    else:
        st.info("סל הארוחה ריק. הוסף פריטים כדי לשמור ארוחה מלאה.")
    st.markdown(
        f'<div style="margin-top:1rem;font-weight:700;font-size:1.1rem;">ארוחות שנשמרו ליום {target_date.isoformat()}</div>',
        unsafe_allow_html=True,
    )
    saved_logs: list[DailyLogRecord] = [
        DailyLogRecord.model_validate(item)
        for item in cached_daily_logs(user_name=user_name, target_date=target_date)
    ]
    if saved_logs:
        st.dataframe(
            {
                "מאכל": [record.food_name for record in saved_logs],
                "קלוריות": [record.calories_consumed for record in saved_logs],
                "נפילה": ["כן" if record.is_fail else "לא" for record in saved_logs],
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("אין עדיין ארוחות שמורות לתאריך הזה.")


def render_progress_page(user_name: str) -> None:
    """Render progress placeholder page."""
    st.markdown('<div class="title">התקדמות</div>', unsafe_allow_html=True)
    progress_date: date = st.date_input("בחר תאריך למעקב", value=date.today(), key="progress_date")
    summary: DailySummary = DailySummary.model_validate(
        cached_daily_summary(user_name=user_name, target_date=progress_date)
    )
    st.metric("סה\"כ קלוריות היום", summary.total_calories)
    st.metric("נותר ליעד", summary.remaining_calories)
    st.info("בקרוב: גרפים ומעקב מגמות.")


def render_settings_page(user_name: str) -> None:
    """Render settings page with user profile and goals."""
    st.markdown('<div class="title">הגדרות</div>', unsafe_allow_html=True)
    service: NutritionService = get_service()
    st.write(f"**משתמש מחובר:** {user_name}")
    st.write(f"**יעד קלורי יומי:** {service.get_daily_goal(user_name)}")
    if st.button("התנתקות", use_container_width=True):
        st.session_state.logged_in_user = None
        st.session_state.meal_basket = []
        st.rerun()


def main() -> None:
    """Run Streamlit presentation entry point."""
    st.markdown(APP_CSS, unsafe_allow_html=True)

    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None
    if "meal_basket" not in st.session_state:
        st.session_state.meal_basket = []

    if st.session_state.logged_in_user is None:
        render_login()
        st.stop()

    current_user: str = str(st.session_state.logged_in_user)
    selected_page: str = st.sidebar.radio(
        "ניווט",
        options=["יומן ארוחות", "התקדמות", "הגדרות"],
        index=0,
    )
    try:
        with st.spinner("טוען נתונים..."):
            if selected_page == "יומן ארוחות":
                render_dashboard(current_user)
            elif selected_page == "התקדמות":
                render_progress_page(current_user)
            else:
                render_settings_page(current_user)
        st.markdown('<div class="footer-meta">Manage app</div>', unsafe_allow_html=True)
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