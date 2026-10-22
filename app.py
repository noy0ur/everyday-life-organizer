import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "life_organizer.db"
PRIORITIES = ["Low", "Medium", "High"]
TASK_STATUSES = ["Not started", "In progress", "Done"]
CATEGORIES = ["Personal", "Work", "Study", "Health", "Home", "Shopping", "Other"]

st.set_page_config(page_title="Everyday Life Organizer", page_icon="🗓️", layout="wide")

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            due_date TEXT,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Not started',
            details TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopping_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantity TEXT DEFAULT '1',
            checked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Unpaid',
            note TEXT DEFAULT ''
        )
    """)
    conn.commit()
    return conn

def query_df(sql, params=()):
    conn = connect()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = connect()
    conn.execute(sql, params)
    conn.commit()
    conn.close()

def now_text():
    return datetime.now().isoformat(timespec="seconds")

def fmt_date(value):
    if not value:
        return "No due date"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return value

st.title("🗓️ Everyday Life Organizer")
st.write("One simple place to organize tasks, notes, shopping lists, and upcoming bills.")
st.caption("A practical personal productivity app built with Python, Streamlit, Pandas, and SQLite.")

tasks = query_df("SELECT * FROM tasks")
bills = query_df("SELECT * FROM bills")
today = date.today().isoformat()
open_tasks = tasks[tasks["status"] != "Done"] if not tasks.empty else tasks
overdue_tasks = open_tasks[(open_tasks["due_date"].fillna("") != "") & (open_tasks["due_date"] < today)] if not open_tasks.empty else open_tasks
unpaid_bills = bills[bills["status"] == "Unpaid"] if not bills.empty else bills
due_bills = unpaid_bills[unpaid_bills["due_date"] <= (date.today() + timedelta(days=7)).isoformat()] if not unpaid_bills.empty else unpaid_bills

m1, m2, m3, m4 = st.columns(4)
m1.metric("Open tasks", len(open_tasks))
m2.metric("Overdue tasks", len(overdue_tasks))
m3.metric("Unpaid bills", len(unpaid_bills))
m4.metric("Bills due in 7 days", len(due_bills))

tab_tasks, tab_notes, tab_shopping, tab_bills = st.tabs(
    ["✅ Tasks", "📝 Notes", "🛒 Shopping list", "💳 Bills"]
)

with tab_tasks:
    st.subheader("Add a task")
    with st.form("add_task", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Task title *", placeholder="e.g. Submit assignment")
        category = c2.selectbox("Category", CATEGORIES)
        c3, c4 = st.columns(2)
        due = c3.date_input("Due date (optional)", value=None)
        priority = c4.selectbox("Priority", PRIORITIES, index=1)
        details = st.text_area("Details (optional)", max_chars=1000)
        add_task = st.form_submit_button("Add task", use_container_width=True)
    if add_task:
        if not title.strip():
            st.error("Enter a task title.")
        else:
            due_value = due.isoformat() if due else None
            execute(
                "INSERT INTO tasks (title, category, due_date, priority, status, details, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title.strip(), category, due_value, priority, "Not started", details.strip(), now_text())
            )
            st.success("Task added.")
            st.rerun()

    st.subheader("Your tasks")
    task_df = query_df("SELECT * FROM tasks ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, due_date")
    if task_df.empty:
        st.info("No tasks yet. Add your first task above.")
    else:
        status_filter = st.multiselect("Show statuses", TASK_STATUSES, default=TASK_STATUSES)
        view = task_df[task_df["status"].isin(status_filter)].copy()
        for _, row in view.iterrows():
            with st.container(border=True):
                left, mid, right = st.columns([3, 2, 1])
                left.markdown(f"**{row['title']}**")
                left.caption(f"{row['category']} · Due: {fmt_date(row['due_date'])} · Priority: {row['priority']}")
                if row["details"]:
                    left.write(row["details"])
                new_status = mid.selectbox(
                    "Status", TASK_STATUSES,
                    index=TASK_STATUSES.index(row["status"]),
                    key=f"task_status_{row['id']}",
                    label_visibility="collapsed"
                )
                if new_status != row["status"]:
                    execute("UPDATE tasks SET status=? WHERE id=?", (new_status, int(row["id"])))
                    st.rerun()
                if right.button("Delete", key=f"delete_task_{row['id']}"):
                    execute("DELETE FROM tasks WHERE id=?", (int(row["id"]),))
                    st.rerun()
        export_tasks = task_df[["title", "category", "due_date", "priority", "status", "details"]]
        st.download_button("Download tasks CSV", export_tasks.to_csv(index=False).encode("utf-8"), "tasks.csv", "text/csv")

with tab_notes:
    st.subheader("Create a note")
    with st.form("add_note", clear_on_submit=True):
        note_title = st.text_input("Note title *", placeholder="e.g. Ideas for weekend")
        note_content = st.text_area("Note content *", height=140)
        save_note = st.form_submit_button("Save note", use_container_width=True)
    if save_note:
        if not note_title.strip() or not note_content.strip():
            st.error("Enter both a title and note content.")
        else:
            execute("INSERT INTO notes (title, content, updated_at) VALUES (?, ?, ?)", (note_title.strip(), note_content.strip(), now_text()))
            st.success("Note saved.")
            st.rerun()
    note_df = query_df("SELECT * FROM notes ORDER BY updated_at DESC")
    st.subheader("Saved notes")
    if note_df.empty:
        st.info("Your notes will appear here.")
    else:
        for _, row in note_df.iterrows():
            with st.expander(f"📝 {row['title']} · {row['updated_at'][:10]}"):
                st.write(row["content"])
                if st.button("Delete note", key=f"delete_note_{row['id']}"):
                    execute("DELETE FROM notes WHERE id=?", (int(row["id"]),))
                    st.rerun()

with tab_shopping:
    st.subheader("Shopping list")
    with st.form("add_shopping", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        item = c1.text_input("Item *", placeholder="e.g. Milk")
        quantity = c2.text_input("Quantity", value="1")
        add_item = st.form_submit_button("Add item", use_container_width=True)
    if add_item:
        if not item.strip():
            st.error("Enter an item name.")
        else:
            execute("INSERT INTO shopping_items (item, quantity, checked, created_at) VALUES (?, ?, 0, ?)", (item.strip(), quantity.strip() or "1", now_text()))
            st.rerun()
    shopping_df = query_df("SELECT * FROM shopping_items ORDER BY checked, id DESC")
    if shopping_df.empty:
        st.info("Your shopping list is empty.")
    else:
        for _, row in shopping_df.iterrows():
            c1, c2, c3 = st.columns([4, 2, 1])
            checked = c1.checkbox(f"{row['item']} ({row['quantity']})", value=bool(row["checked"]), key=f"shop_{row['id']}")
            if int(checked) != int(row["checked"]):
                execute("UPDATE shopping_items SET checked=? WHERE id=?", (int(checked), int(row["id"])))
                st.rerun()
            c2.write("Purchased" if checked else "To buy")
            if c3.button("Remove", key=f"remove_shop_{row['id']}"):
                execute("DELETE FROM shopping_items WHERE id=?", (int(row["id"]),))
                st.rerun()
        remaining = shopping_df[shopping_df["checked"] == 0][["item", "quantity"]]
        st.download_button("Download remaining shopping list", remaining.to_csv(index=False).encode("utf-8"), "shopping-list.csv", "text/csv")

with tab_bills:
    st.subheader("Track a bill or payment")
    with st.form("add_bill", clear_on_submit=True):
        c1, c2 = st.columns(2)
        bill_name = c1.text_input("Bill name *", placeholder="e.g. Internet")
        bill_amount = c2.number_input("Amount (₹)", min_value=0.0, value=500.0, step=100.0)
        c3, c4 = st.columns(2)
        bill_due = c3.date_input("Due date", value=date.today(), key="bill_due")
        bill_note = c4.text_input("Note (optional)")
        add_bill = st.form_submit_button("Add bill", use_container_width=True)
    if add_bill:
        if not bill_name.strip() or bill_amount <= 0:
            st.error("Enter a bill name and an amount greater than zero.")
        else:
            execute("INSERT INTO bills (name, amount, due_date, status, note) VALUES (?, ?, ?, 'Unpaid', ?)", (bill_name.strip(), float(bill_amount), bill_due.isoformat(), bill_note.strip()))
            st.success("Bill added.")
            st.rerun()
    bill_df = query_df("SELECT * FROM bills ORDER BY status, due_date")
    if bill_df.empty:
        st.info("No bills recorded yet.")
    else:
        for _, row in bill_df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['name']}**")
                c1.caption(f"Due {fmt_date(row['due_date'])}" + (f" · {row['note']}" if row["note"] else ""))
                c2.write(f"₹{row['amount']:,.2f} · {row['status']}")
                new_status = "Paid" if row["status"] == "Unpaid" else "Unpaid"
                if c3.button(f"Mark {new_status.lower()}", key=f"bill_status_{row['id']}"):
                    execute("UPDATE bills SET status=? WHERE id=?", (new_status, int(row["id"])))
                    st.rerun()
                if st.button("Delete bill", key=f"delete_bill_{row['id']}"):
                    execute("DELETE FROM bills WHERE id=?", (int(row["id"]),))
                    st.rerun()
        unpaid_total = bill_df.loc[bill_df["status"] == "Unpaid", "amount"].sum()
        st.metric("Total unpaid bills", f"₹{unpaid_total:,.2f}")
        st.download_button("Download bills CSV", bill_df.drop(columns=["id"]).to_csv(index=False).encode("utf-8"), "bills.csv", "text/csv")

st.divider()
st.caption("Privacy: this demo stores data in a local SQLite file. It has no login or cloud sync. Do not store passwords, bank details, or highly sensitive information. On some free cloud hosts, local database data may reset after redeployment.")
