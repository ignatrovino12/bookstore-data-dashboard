import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from llm_service import create_chat, send_message

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=600)

st.set_page_config( page_title="Store Analytics", layout="wide")
st.title("Store Analytics")
dashboard_tab, assistant_tab = st.tabs(["Dashboard", "AI Assistant"])

def show_daily_revenue(
    store_id,
    engine,
    top_days=5,
    start_date=None,
    end_date=None,
    granularity="day",
):
    period_expression = {
        "day": "DATE(timestamp)",
        "week": "DATE_TRUNC('week', timestamp)::date",
        "month": "DATE_TRUNC('month', timestamp)::date",
    }[granularity]
    where_clauses = ["store_id = :store_id"]
    params = {"store_id": store_id}
    if start_date is not None:
        where_clauses.append("DATE(timestamp) >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        where_clauses.append("DATE(timestamp) <= :end_date")
        params["end_date"] = end_date
    query = text(f"""
        SELECT
            {period_expression} AS period_start,
            SUM(paid_price) AS revenue
        FROM orders
        WHERE {" AND ".join(where_clauses)}
        GROUP BY period_start
        ORDER BY revenue DESC
    """)

    with engine.connect() as connection:
        revenue = pd.read_sql(
            query,
            connection,
            params=params,
        )

    revenue_sorted = revenue.sort_values("period_start")
    period_label = {"day": "days", "week": "weeks", "month": "months"}[granularity]
    st.line_chart(
        revenue_sorted,
        x="period_start",
        y="revenue",
        x_label=granularity.title(),
        y_label="Revenue",
        color="green",
    )
    st.subheader(f"Top {top_days} {period_label} by revenue")
    st.dataframe(revenue.head(top_days), width="stretch", hide_index=True)

def get_real_customer_groups(store_id, engine):
    query = text("""
        SELECT id, source_id, name, address, phone, email
        FROM users
        WHERE store_id = :store_id
    """)

    with engine.connect() as connection:
        users = pd.read_sql(query, connection, params={"store_id": store_id})

    columns = ["name", "address", "phone", "email"]
    users[columns] = users[columns].apply(lambda col: col.astype("string").str.strip().str.casefold())
    users = users.astype(object).where(users.notna(), None)

    seen = [{} for _ in range(4)]
    group_ids = []
    next_group = 0
    for values in users[columns].itertuples(index=False, name=None):
        group = None

        for omitted in range(4):
            key = values[:omitted] + values[omitted + 1:]
            if all(value is not None for value in key):
                if key in seen[omitted]:
                    group = seen[omitted][key]
                    break

        if group is None:
            group = next_group
            next_group += 1
        group_ids.append(group)

        for omitted in range(4):
            key = values[:omitted] + values[omitted + 1:]
            if all(value is not None for value in key):
                seen[omitted].setdefault(key, group)

    users["customer_group"] = group_ids
    return users


def count_real_users(store_id, engine):
    users = get_real_customer_groups(store_id, engine)
    unique_count = users["customer_group"].nunique()
    duplicates = len(users) - unique_count

    return unique_count, duplicates

def find_top_customer(store_id, engine):
    users = get_real_customer_groups(store_id, engine)

    query = text("""
        SELECT user_id, SUM(paid_price) AS total_spent_money
        FROM orders
        WHERE store_id = :store_id
        GROUP BY user_id
    """)

    with engine.connect() as connection:
        spent_money = pd.read_sql(query, connection, params={"store_id": store_id})

    users = users.merge( spent_money, left_on="source_id", right_on="user_id", how="left")
    customers = users.groupby("customer_group").agg(
            user_ids=("source_id", lambda ids: list(ids)),
            total_spent_money=("total_spent_money", "sum")
        )
    
    return customers[customers["total_spent_money"] == customers["total_spent_money"].max()]

def count_authors(store_id, engine):
    query = text("""
        SELECT book_id, author_id
        FROM book_authors
        WHERE store_id = :store_id
        ORDER BY book_id, author_id
    """)

    with engine.connect() as connection:
        df = pd.read_sql(query, connection, params={"store_id": store_id})

    author_groups = (df.groupby("book_id")["author_id"].apply(lambda authors: tuple(sorted(set(authors)))))
    unique_groups = author_groups.nunique()

    return unique_groups

def find_most_popular_author(store_id, engine):
    query_books = text("""
        SELECT
            b.source_id AS book_id,
            SUM(o.quantity) AS sold_count
        FROM books b
        JOIN orders o
            ON o.book_id = b.source_id
            AND o.store_id = b.store_id
        WHERE b.store_id = :store_id
        GROUP BY b.id
    """)

    query_authors = text("""
        SELECT
            ba.book_id,
            ba.author_id,
            a.author_name
        FROM book_authors ba
        JOIN authors a
            ON a.author_id = ba.author_id
        WHERE ba.store_id = :store_id
    """)

    with engine.connect() as connection:
        book_sales = pd.read_sql(query_books, connection, params={"store_id": store_id})
        author_data = pd.read_sql(query_authors, connection, params={"store_id": store_id})

    author_groups = author_data.groupby("book_id")["author_id"].apply(lambda authors: tuple(sorted(set(authors)))).rename("author_group").reset_index()
    book_sales = book_sales.merge(author_groups, on="book_id", how="inner")
    group_sales = book_sales.groupby("author_group")["sold_count"].sum().reset_index()
    max_sales = group_sales["sold_count"].max()

    top_groups = group_sales[group_sales["sold_count"] == max_sales].copy()
    author_names = author_data.drop_duplicates("author_id").set_index("author_id")["author_name"].to_dict()
    top_groups["authors"] = top_groups["author_group"].apply(lambda ids: [author_names[author_id] for author_id in ids])

    return top_groups[["authors", "sold_count"]].sort_values("sold_count", ascending=False)

if "dashboard_top_days" not in st.session_state:
    st.session_state["dashboard_top_days"] = 5

for setting_key, default_value in {
    "dashboard_start_date": None,
    "dashboard_end_date": None,
    "dashboard_granularity": "day",
}.items():
    if setting_key not in st.session_state:
        st.session_state[setting_key] = default_value

if "dashboard_store_selector" not in st.session_state:
    st.session_state["dashboard_store_selector"] = (
        st.session_state.get("dashboard_store_id", 1))

if "pending_dashboard_store_id" in st.session_state:
    new_store_id = st.session_state.pop("pending_dashboard_store_id")
    st.session_state["dashboard_store_selector"] = new_store_id

if "pending_dashboard_settings" in st.session_state:
    pending_settings = st.session_state.pop("pending_dashboard_settings")
    for setting_key, setting_value in pending_settings.items():
        st.session_state[setting_key] = setting_value

with dashboard_tab:
    store_id = st.selectbox(
        "Select a store",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: f"Store {x}",
        key="dashboard_store_selector",
    )

    top_days = st.session_state["dashboard_top_days"]
    start_date = st.session_state["dashboard_start_date"]
    end_date = st.session_state["dashboard_end_date"]
    granularity = st.session_state["dashboard_granularity"]
    st.write(f"Selected store: {store_id}")
    st.header(f"Store {store_id} Overview")

    st.subheader("Revenue")
    if start_date is not None or end_date is not None:
        st.caption(
            "Revenue date range: "
            f"{start_date.isoformat() if start_date else 'all dates'} to "
            f"{end_date.isoformat() if end_date else 'all dates'} "
            "(inclusive)"
        )
    if start_date is not None and end_date is not None and start_date > end_date:
        st.error("Start date must be on or before end date.")
    else:
        show_daily_revenue(
            store_id,
            engine,
            top_days,
            start_date,
            end_date,
            granularity,
        )
    st.divider()

    st.subheader("Customer Overview")
    real_users, duplicates = count_real_users(store_id, engine)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Unique users", real_users)
    with col2:
        st.metric("Duplicate user records", duplicates)

    st.caption("Customer with the highest total spending")
    top_customer = find_top_customer(store_id, engine)
    st.dataframe(top_customer, width="stretch", hide_index=True)
    st.divider()

    st.subheader("Authors Overview")
    unique_author_sets = count_authors(store_id, engine)
    st.metric("Unique sets of authors", unique_author_sets)

    st.caption("Author group with the highest book sales")
    best_author = find_most_popular_author(store_id, engine)
    st.dataframe(best_author, width = 'stretch', hide_index=True)
    st.divider()

with assistant_tab:
    st.header("AI Assistant")
   
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = []
    if "llm_chat" not in st.session_state:
        st.session_state.llm_chat = create_chat()
    if st.button("Reset chat"):
        st.session_state.llm_chat = create_chat()
        st.session_state.assistant_messages = []
        st.rerun()

    for message in st.session_state.assistant_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if question := st.chat_input("Ask a question about the stores..."):
        st.session_state.assistant_messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        message_completed = False
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = send_message(st.session_state.llm_chat, question)
                    st.markdown(answer)
                    st.session_state.assistant_messages.append({"role": "assistant", "content": answer})
                    message_completed = True

                except Exception as e:
                    st.exception(e)

        if message_completed and st.session_state.pop("dashboard_update_pending", False):
            st.rerun()
