import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# הגדרות עיצוב
st.set_page_config(page_title="דיאטה זוגית - רחמים & אורלי", layout="centered")

# --- אתחול נתונים ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['user', 'food', 'calories', 'date', 'time', 'is_fail'])
if 'targets' not in st.session_state:
    st.session_state.targets = {"רחמים": 2500, "אורלי": 2000}
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# --- פונקציית התנתקות ---
def logout():
    st.session_state.logged_in_user = None
    st.rerun()

# --- מסך כניסה (Login) ---
if st.session_state.logged_in_user is None:
    st.markdown("<h1 style='text-align: center;'>שלום! מי נכנס היום?</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🙋‍♂️ רחמים", use_container_width=True):
            st.session_state.logged_in_user = "רחמים"
            st.rerun()
    with col2:
        if st.button("🙋‍♀️ אורלי", use_container_width=True):
            st.session_state.logged_in_user = "אורלי"
            st.rerun()
    st.stop() # עוצר את הרצת הקוד עד שבוחרים משתמש

# --- תפריט ניווט צדדי ---
current_user = st.session_state.logged_in_user
st.sidebar.title(f"שלום, {current_user}!")
page = st.sidebar.radio("עבור לדף:", ["היומן היומי", "יומן שבועי", "הגדרות יעד"])
if st.sidebar.button("החלף משתמש 🔄"):
    logout()

# --- דף 1: היומן היומי ---
if page == "היומן היומי":
    st.markdown(f"<h2 style='text-align: center;'>היומן של {current_user}</h2>", unsafe_allow_html=True)
    
    # חישוב נתונים להיום
    today = datetime.now().strftime("%Y-%m-%d")
    today_df = st.session_state.data[(st.session_state.data['date'] == today) & (st.session_state.data['user'] == current_user)]
    total_today = today_df['calories'].sum()
    target = st.session_state.targets[current_user]
    
    # תצוגה ויזואלית
    st.metric("קלוריות שנאכלו היום", f"{total_today} / {target}")
    progress = min(total_today / target, 1.0) if target > 0 else 0
    st.progress(progress)

    st.divider()
    
    # טופס הוספה
    with st.form("add_meal", clear_on_submit=True):
        food = st.text_input("מה אכלת?")
        cals = st.number_input("כמות קלוריות", min_value=0, step=50)
        fail = st.toggle("נפילה? 😢")
        if st.form_submit_button("עדכן יומן 🚀", use_container_width=True):
            new_row = {
                'user': current_user,
                'food': food if not fail else "נפילה 😢",
                'calories': cals,
                'date': today,
                'time': datetime.now().strftime("%H:%M"),
                'is_fail': fail
            }
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

    # רשימת ארוחות מהיום
    if not today_df.empty:
        st.write("### ארוחות מהיום:")
        for _, row in today_df[::-1].iterrows():
            st.info(f"🕒 {row['time']} | {row['food']} - {row['calories']} קלוריות")

# --- דף 2: יומן שבועי ---
elif page == "יומן שבועי":
    st.header("📅 סיכום שבועי")
    
    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    weekly_df = st.session_state.data[st.session_state.data['date'] >= last_week]
    
    if weekly_df.empty:
        st.write("עדיין אין נתונים לשבוע האחרון.")
    else:
        # סיכום לפי ימים ומשתמש
        st.write("פירוט ארוחות מלא:")
        # הפיכת הטבלה לקריאה יותר
        display_df = weekly_df[['date', 'time', 'user', 'food', 'calories']].sort_values(by=['date', 'time'], ascending=False)
        st.dataframe(display_df, use_container_width=True)
        
        # גרף פשוט (אופציונלי)
        st.bar_chart(weekly_df.groupby('date')['calories'].sum())

# --- דף 3: הגדרות יעד ---
elif page == "הגדרות יעד":
    st.header("⚙️ הגדרות אישיות")
    new_target = st.select_slider(f"שנה יעד יומי ל{current_user}:", options=list(range(1000, 8001, 100)), value=st.session_state.targets[current_user])
    if st.button("שמור יעד 🎯"):
        st.session_state.targets[current_user] = new_target
        st.success("היעד עודכן בהצלחה!")