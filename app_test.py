import streamlit as st
import sqlite3
import pandas as pd

DB_PATH = "bridges5.db"

CHILD_TABLES = [
    "features",
    "span_sets",
    "substructure_sets",
    "elements",
    "inspections",
    "posting_evaluations",
    "posting_statuses",
    "works"
]

# ----------------------------
# Database helpers
# ----------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def update_bridge_id(old_state, old_bridge, new_state, new_bridge):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")

        for table in CHILD_TABLES:
            cur.execute(f"""
                UPDATE {table}
                SET state_code=?, bridge_number=?
                WHERE state_code=? AND bridge_number=?
            """, (new_state, new_bridge, old_state, old_bridge))

        cur.execute("""
            UPDATE bridges
            SET state_code=?, bridge_number=?
            WHERE state_code=? AND bridge_number=?
        """, (new_state, new_bridge, old_state, old_bridge))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def load_table(query, params=()):
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def save_table(df, table, state_code, bridge_number):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
        DELETE FROM {table}
        WHERE state_code=? AND bridge_number=?
    """, (state_code, bridge_number))

    df.to_sql(table, conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

# ----------------------------
# UI
# ----------------------------
st.set_page_config(layout="wide")
st.title("SNBI Bridge Database Editor")

# ----------------------------
# Select bridge
# ----------------------------
bridges_df = load_table("""
    SELECT state_code, bridge_number, bridge_name
    FROM bridges
    ORDER BY state_code, bridge_number
""")

if bridges_df.empty:
    st.warning("No bridges found.")
    st.stop()

selected = st.selectbox(
    "Select Bridge",
    bridges_df.itertuples(index=False),
    format_func=lambda x: f"{x.state_code}-{x.bridge_number} | {x.bridge_name}"
)

old_state = selected.state_code
old_bridge = selected.bridge_number

bridge = load_table("""
    SELECT * FROM bridges
    WHERE state_code=? AND bridge_number=?
""", (old_state, old_bridge)).iloc[0]

# ----------------------------
# Edit main bridge table
# ----------------------------
st.header("Bridge Information")

with st.form("bridge_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        new_state = st.number_input(
            "State Code",
            min_value=1, max_value=99,
            value=int(bridge.state_code)
        )

        year_built = st.number_input(
            "Year Built",
            min_value=0, max_value=9999,
            value=int(bridge.year_built or 0)
        )

    with col2:
        new_bridge = st.text_input(
            "Bridge Number",
            value=bridge.bridge_number
        )

        bridge_name = st.text_input(
            "Bridge Name",
            value=bridge.bridge_name or ""
        )

    with col3:
        nbis_length = st.number_input(
            "NBIS Bridge Length",
            min_value=0.0,
            value=float(bridge.nbis_bridge_length or 0.0)
        )

    change_id = st.checkbox("Allow changing Bridge ID (State / Number)")

    submit_bridge = st.form_submit_button("Save Bridge")

if submit_bridge:
    conn = get_connection()
    cur = conn.cursor()

    try:
        if change_id and (new_state, new_bridge) != (old_state, old_bridge):
            update_bridge_id(old_state, old_bridge, new_state, new_bridge)

        cur.execute("""
            UPDATE bridges
            SET bridge_name=?,
                nbis_bridge_length=?,
                year_built=?
            WHERE state_code=? AND bridge_number=?
        """, (
            bridge_name,
            nbis_length,
            year_built,
            new_state,
            new_bridge
        ))

        conn.commit()
        st.success("Bridge updated successfully")
        st.experimental_rerun()

    except Exception as e:
        conn.rollback()
        st.error(f"Update failed: {e}")
    finally:
        conn.close()

# ----------------------------
# Child tables editor
# ----------------------------
st.header("Related Tables")

tabs = st.tabs(CHILD_TABLES)

for tab, table in zip(tabs, CHILD_TABLES):
    with tab:
        df = load_table(
            f"SELECT * FROM {table} WHERE state_code=? AND bridge_number=?",
            (new_state, new_bridge)
        )

        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key=table
        )

        if st.button(f"Save {table}", key=f"save_{table}"):
            try:
                save_table(edited_df, table, new_state, new_bridge)
                st.success(f"{table} saved successfully")
            except Exception as e:
                st.error(f"Failed to save {table}: {e}")
