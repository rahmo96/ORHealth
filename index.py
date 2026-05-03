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
from app.database.users_repository import UsersRepository
from app.models.schemas import DailyLogRecord, DailySummary, FoodItem, MealBasketItem, User
from app.services.nutrition_service import NutritionService
from app.ui.styles import inject_global_styles

st.set_page_config(page_title="ORHealth", page_icon="🍏", layout="centered")
configure_logging()
LOGGER: logging.Logger = logging.getLogger(__name__)

PAGE_JOURNAL: str = "יומן ארוחות"
PAGE_PROGRESS: str = "התקדמות"
PAGE_SETTINGS: str = "הגדרות"
NAV_PAGES: tuple[str, ...] = (PAGE_JOURNAL, PAGE_PROGRESS, PAGE_SETTINGS)


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
    users_repository = UsersRepository(connection=connection)
    return NutritionService(repository=repository, users_repository=users_repository)


@st.cache_data(ttl=300, show_spinner=False)
def cached_food_catalog() -> list[dict[str, Any]]:
    """Return cached food catalog as serializable dictionaries."""
    return [item.model_dump() for item in get_service().get_food_catalog()]


@st.cache_data(ttl=300, show_spinner=False)
def cached_users() -> list[dict[str, Any]]:
    """Return cached user roster as serializable dictionaries."""
    return [user.model_dump() for user in get_service().list_users()]


@st.cache_data(ttl=15, show_spinner=False)
def cached_journal_day(
    user_name: str, target_date: date, user_id: int | None = None
) -> dict[str, Any]:
    """Return logs + summary for one day in a single DB round-trip (cached briefly)."""
    logs, summary = get_service().get_journal_for_day(
        user_name=user_name, target_date=target_date, user_id=user_id
    )
    return {
        "logs": [record.model_dump(mode="json") for record in logs],
        "summary": summary.model_dump(),
    }


USER_AVATARS: dict[str, str] = {"רחמים": "🙋‍♂️", "אורלי": "🙋‍♀️"}


def _user_button_label(user: User) -> str:
    """Return a friendly button label for a user, including a default avatar."""
    avatar: str = USER_AVATARS.get(user.display_name, "👤")
    return f"{avatar} {user.display_name}"


def render_login() -> None:
    """Render the 2-step login: pick user, then enter / set PIN."""
    try:
        user_dicts: list[dict[str, Any]] = cached_users()
    except DatabaseAppError:
        raise
    users: list[User] = [User.model_validate(item) for item in user_dicts]

    selected_name: str | None = st.session_state.get("login_selected_user")
    selected_user: User | None = next(
        (u for u in users if u.display_name == selected_name), None
    )

    if selected_user is None:
        _render_user_picker(users)
        return

    _render_pin_step(selected_user)


def _render_user_picker(users: list[User]) -> None:
    """Render the first login step: choosing a user."""
    st.markdown('<div class="title">מי נכנס למערכת? 🍎</div>', unsafe_allow_html=True)
    if not users:
        st.warning("אין משתמשים מוגדרים במערכת. הריצי את מיגרציית ה-SQL.")
        return

    columns = st.columns(min(len(users), 3))
    for index, user in enumerate(users):
        column = columns[index % len(columns)]
        if column.button(
            _user_button_label(user),
            key=f"login_user_{user.id}",
            use_container_width=True,
        ):
            st.session_state.login_selected_user = user.display_name
            st.rerun()


def _render_pin_step(user: User) -> None:
    """Render the second login step: PIN creation or verification."""
    avatar: str = USER_AVATARS.get(user.display_name, "👤")
    st.markdown(
        f'<div class="title">{avatar} שלום {user.display_name}</div>',
        unsafe_allow_html=True,
    )

    if st.button("← בחר משתמש אחר", key="login_back_to_picker"):
        st.session_state.login_selected_user = None
        st.rerun()

    service: NutritionService = get_service()

    if not user.has_pin:
        st.info("המשתמש שלך עדיין ללא קוד סודי. צרי קוד חדש כדי להמשיך.")
        with st.form("login_create_pin"):
            new_pin: str = st.text_input(
                "קוד סודי חדש (4-6 ספרות)", type="password", max_chars=6
            )
            confirm_pin: str = st.text_input(
                "אישור קוד סודי", type="password", max_chars=6
            )
            submitted: bool = st.form_submit_button("שמירת קוד והכניסה ✅", use_container_width=True)
        if submitted:
            if new_pin != confirm_pin:
                st.toast("הקודים לא תואמים", icon="⚠️")
                return
            try:
                service.set_pin(user_id=user.id, pin=new_pin)
            except ValidationAppError:
                st.toast("הקוד חייב להיות 4-6 ספרות", icon="🚫")
                return
            except DatabaseAppError:
                LOGGER.exception("Failed to set PIN.")
                st.toast("שמירת קוד נכשלה", icon="🔥")
                return
            cached_users.clear()
            _set_logged_in_user(user)
            st.toast("הקוד נשמר. ברוכים הבאים!", icon="🎉")
            st.rerun()
        return

    with st.form("login_verify_pin"):
        pin_value: str = st.text_input("קוד סודי", type="password", max_chars=6)
        submitted = st.form_submit_button("כניסה ✅", use_container_width=True)
    if submitted:
        try:
            authenticated: User = service.authenticate(
                display_name=user.display_name, pin=pin_value
            )
        except ValidationAppError as error:
            LOGGER.info("Login failed for user %s: %s", user.display_name, error)
            st.toast("קוד שגוי", icon="🚫")
            return
        except DatabaseAppError:
            LOGGER.exception("DB error during authenticate.")
            st.toast("שגיאת מסד נתונים בכניסה", icon="🔥")
            return
        _set_logged_in_user(authenticated)
        st.toast("ברוכים הבאים!", icon="🎉")
        st.rerun()


def _set_logged_in_user(user: User) -> None:
    """Persist the authenticated user in session state."""
    st.session_state.logged_in_user = user.display_name
    st.session_state.logged_in_user_id = user.id
    st.session_state.login_selected_user = None


def render_dashboard(user_name: str, user_id: int | None) -> None:
    """Render meal journal with basket and batch save."""
    st.markdown(f'<div class="title">היומן של {user_name}</div>', unsafe_allow_html=True)
    target_date: date = st.date_input("בחר יום ביומן", value=date.today(), format="YYYY-MM-DD")
    foods: list[FoodItem] = [
        FoodItem.model_validate(item) for item in cached_food_catalog()
    ]
    food_options: list[str] = [item.food_name for item in foods]
    calories_by_food: dict[str, int] = {item.food_name: item.default_calories for item in foods}

    journal: dict[str, Any] = cached_journal_day(
        user_name=user_name, target_date=target_date, user_id=user_id
    )
    summary: DailySummary = DailySummary.model_validate(journal["summary"])
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
            column_config={
                "מאכל": st.column_config.TextColumn(alignment="right"),
                "קלוריות": st.column_config.NumberColumn(alignment="right"),
                "נפילה": st.column_config.TextColumn(alignment="right"),
            },
        )
        control_col1, control_col2 = st.columns(2)
        if control_col1.button("שמור ארוחה מלאה ✅", use_container_width=True):
            with st.status("שומר את כל הסל...", expanded=False) as status:
                try:
                    get_service().add_full_meal(
                        user_name=user_name, items=basket_items, user_id=user_id
                    )
                    st.session_state.meal_basket = [
                        item.model_dump()
                        for item in basket_items_all
                        if item.meal_date != target_date
                    ]
                    cached_journal_day.clear()
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
        f'<div style="margin-top:1rem;font-weight:700;font-size:1.1rem;text-align:right;direction:rtl;">'
        f"ארוחות שנשמרו ליום {target_date.isoformat()}</div>",
        unsafe_allow_html=True,
    )
    saved_logs: list[DailyLogRecord] = [
        DailyLogRecord.model_validate(item) for item in journal["logs"]
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
            column_config={
                "מאכל": st.column_config.TextColumn(alignment="right"),
                "קלוריות": st.column_config.NumberColumn(alignment="right"),
                "נפילה": st.column_config.TextColumn(alignment="right"),
            },
        )
    else:
        st.caption("אין עדיין ארוחות שמורות לתאריך הזה.")


def render_progress_page(user_name: str, user_id: int | None) -> None:
    """Render progress placeholder page."""
    st.markdown('<div class="title">התקדמות</div>', unsafe_allow_html=True)
    progress_date: date = st.date_input("בחר תאריך למעקב", value=date.today(), key="progress_date")
    journal: dict[str, Any] = cached_journal_day(
        user_name=user_name, target_date=progress_date, user_id=user_id
    )
    summary: DailySummary = DailySummary.model_validate(journal["summary"])
    st.metric("סה\"כ קלוריות היום", summary.total_calories)
    st.metric("נותר ליעד", summary.remaining_calories)
    st.info("בקרוב: גרפים ומעקב מגמות.")


def render_settings_page(user_name: str, user_id: int | None) -> None:
    """Render settings page with user profile, daily goal, and PIN management."""
    st.markdown('<div class="title">הגדרות</div>', unsafe_allow_html=True)
    service: NutritionService = get_service()
    current_goal: int = service.get_daily_goal(user_name)
    st.write(f"**משתמש מחובר:** {user_name}")
    st.write(f"**יעד קלורי יומי:** {current_goal}")

    if user_id is None:
        st.info("עדכון יעד וקוד סודי דורש מיגרציה של טבלת users.")
    else:
        with st.form("settings_goal_form"):
            new_goal: int = st.number_input(
                "יעד קלוריות יומי",
                min_value=500,
                max_value=10000,
                value=int(current_goal),
                step=50,
            )
            goal_submitted: bool = st.form_submit_button(
                "שמירת יעד", use_container_width=True
            )
        if goal_submitted:
            try:
                service.update_daily_goal(user_id=user_id, goal=int(new_goal))
            except ValidationAppError:
                st.toast("יעד לא תקין", icon="🚫")
            except DatabaseAppError:
                LOGGER.exception("Failed to update daily goal.")
                st.toast("שמירת יעד נכשלה", icon="🔥")
            else:
                cached_users.clear()
                cached_journal_day.clear()
                st.toast("היעד עודכן בהצלחה", icon="🎯")
                st.rerun()

        with st.form("settings_pin_form"):
            new_pin: str = st.text_input(
                "קוד סודי חדש (4-6 ספרות)", type="password", max_chars=6
            )
            confirm_pin: str = st.text_input(
                "אישור קוד סודי", type="password", max_chars=6
            )
            pin_submitted: bool = st.form_submit_button(
                "שינוי קוד סודי", use_container_width=True
            )
        if pin_submitted:
            if new_pin != confirm_pin:
                st.toast("הקודים לא תואמים", icon="⚠️")
            else:
                try:
                    service.set_pin(user_id=user_id, pin=new_pin)
                except ValidationAppError:
                    st.toast("הקוד חייב להיות 4-6 ספרות", icon="🚫")
                except DatabaseAppError:
                    LOGGER.exception("Failed to change PIN.")
                    st.toast("שינוי קוד נכשל", icon="🔥")
                else:
                    cached_users.clear()
                    st.toast("הקוד עודכן בהצלחה", icon="🔐")

    if st.button("התנתקות", use_container_width=True):
        st.session_state.logged_in_user = None
        st.session_state.logged_in_user_id = None
        st.session_state.login_selected_user = None
        st.session_state.meal_basket = []
        st.rerun()

    st.subheader("קטלוג מאכלים")
    st.caption(
        "הוספת מאכל חדש לטבלת foods_master: שם ייחודי וקלוריות ברירת מחדל (כפי שמוצגים ביומן)."
    )
    with st.form("foods_master_add_form"):
        new_food_name: str = st.text_input(
            "שם המאכל",
            max_chars=120,
            placeholder="למשל: סלט ירקות",
        )
        new_food_calories: int = st.number_input(
            "קלוריות ברירת מחדל",
            min_value=1,
            max_value=10000,
            value=200,
            step=1,
        )
        add_catalog_submitted: bool = st.form_submit_button(
            "הוספה לקטלוג",
            use_container_width=True,
        )
    if add_catalog_submitted:
        try:
            service.add_food_catalog_entry(
                food_name=new_food_name,
                default_calories=int(new_food_calories),
            )
        except ValidationAppError as error:
            st.toast(str(error), icon="🚫")
        except DatabaseAppError:
            LOGGER.exception("Failed to add food catalog entry.")
            st.toast("שמירת מאכל לקטלוג נכשלה", icon="🔥")
        else:
            cached_food_catalog.clear()
            st.toast("המאכל נוסף לקטלוג", icon="✅")
            st.rerun()


def render_app_footer() -> None:
    """Optional slim strip above tabs (avoid extra Streamlit markdown blocks—they add mobile height).

    Expand here if you need a persistent link (for example hosting “Manage app”).
    """
    return


def _streamlit_bottom_dock() -> Any:
    """Return Streamlit’s bottom layout slot (viewport-pinned); public `st.bottom` when available."""
    return getattr(st, "bottom", None) or getattr(st, "_bottom", None)


def render_docked_bottom_ui(active_page: str) -> None:
    """Render optional ``render_app_footer`` + compact tabs in Streamlit’s bottom dock.

    Plain CSS `position: fixed` is unreliable inside Streamlit’s transformed layout; the
    dedicated bottom root (`st._bottom`, becoming `st.bottom`) is the supported approach.
    """
    dock: Any = _streamlit_bottom_dock()
    if dock is None:
        render_app_footer()
        render_bottom_navigation(active_page)
        return
    with dock:
        render_app_footer()
        render_bottom_navigation(active_page)


def render_bottom_navigation(active_page: str) -> None:
    """Compact bottom tabs (RTL): one segmented row avoids icon+stacked buttons on phones.

    ``st.segmented_control`` keeps all choices on a single line with far less height than
    three columns × (markdown + full-width buttons). Render inside ``render_docked_bottom_ui``.
    """
    with st.container(border=True):
        selected_raw: Any = st.segmented_control(
            label="כרטיסיות",
            options=list(NAV_PAGES),
            default=active_page,
            key="orhealth_bottom_nav_tabs",
            label_visibility="collapsed",
            width="stretch",
        )
        picked: Any = selected_raw
        if isinstance(picked, (list, tuple)):
            picked = picked[0] if picked else None
        selected: str = picked if isinstance(picked, str) and picked in NAV_PAGES else active_page
        current: str = str(st.session_state.active_page)
        if selected in NAV_PAGES and selected != current:
            st.session_state.active_page = selected
            st.rerun()


def main() -> None:
    """Run Streamlit presentation entry point."""
    inject_global_styles()

    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None
    if "logged_in_user_id" not in st.session_state:
        st.session_state.logged_in_user_id = None
    if "login_selected_user" not in st.session_state:
        st.session_state.login_selected_user = None
    if "meal_basket" not in st.session_state:
        st.session_state.meal_basket = []
    if "active_page" not in st.session_state:
        st.session_state.active_page = PAGE_JOURNAL
    if st.session_state.active_page not in NAV_PAGES:
        st.session_state.active_page = PAGE_JOURNAL

    try:
        if st.session_state.logged_in_user is None:
            render_login()
            st.stop()

        current_user: str = str(st.session_state.logged_in_user)
        current_user_id_raw: Any = st.session_state.logged_in_user_id
        current_user_id: int | None = (
            int(current_user_id_raw) if isinstance(current_user_id_raw, int) else None
        )
        selected_page: str = str(st.session_state.active_page)
        with st.spinner("טוען נתונים..."):
            if selected_page == PAGE_JOURNAL:
                render_dashboard(current_user, current_user_id)
            elif selected_page == PAGE_PROGRESS:
                render_progress_page(current_user, current_user_id)
            else:
                render_settings_page(current_user, current_user_id)
        render_docked_bottom_ui(selected_page)
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