import streamlit as st
from sqlalchemy import text

# 1. אתחול ראשוני - חייב לקרות לפני הכל!
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# 2. חיבור לבסיס הנתונים
conn = st.connection("postgresql", type="sql")

def log_meal(user, food, cals, fail):
    query = """
        INSERT INTO daily_logs (user_name, food_name, calories_consumed, is_fail)
        VALUES (:user, :food, :cals, :fail);
    """
    with conn.session as session:
        session.execute(text(query), {"user": user, "food": food, "cals": cals, "fail": fail})
        session.commit()

# --- לוגיקת כניסה ---
if st.session_state.logged_in_user is None:
    st.title("מי נכנס למערכת? 🍎")
    col1, col2 = st.columns(2)
    if col1.button("🙋‍♂️ רחמים", use_container_width=True):
        st.session_state.logged_in_user = "רחמים"
        st.rerun()
    if col2.button("🙋‍♀️ אורלי", use_container_width=True):
        st.session_state.logged_in_user = "אורלי"
        st.rerun()
    st.stop()

# --- אם הגענו לכאן, המשתמש מחובר ---
# נשמור את השם במשתנה נוח לשימוש
current_user = st.session_state.logged_in_user

st.title(f"היומן של {current_user}")

# שליפת נתונים למילון
food_df = conn.query("SELECT food_name, default_calories FROM foods_master ORDER BY food_name ASC;", ttl="1m")
food_options = food_df['food_name'].tolist() if not food_df.empty else []

# --- טופס הוספת ארוחה ---
with st.form("meal_form", clear_on_submit=True):
    selected_food = st.selectbox("בחר מאכל:", options=[""] + food_options)
    
    # חישוב קלוריות דינמי
    default_cals = 0
    if selected_food:
        default_cals = int(food_df[food_df['food_name'] == selected_food]['default_calories'].iloc[0])
    
    cals = st.number_input("קלוריות:", value=default_cals)
    is_fail = st.toggle("נפילה? 😢")
    
    if st.form_submit_button("שמור ביומן ✅", use_container_width=True):
        if selected_food:
            # תיקון: שולפים את המשתמש ישירות מה-session_state כדי למנוע שגיאות scope
            user_to_log = st.session_state.logged_in_user
            log_meal(user_to_log, selected_food, cals, is_fail)
            st.success(f"נרשם בהצלחה!")
            st.rerun()
        else:
            st.error("אנא בחר מאכל")