import os
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import streamlit as st

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def get_book_count(store_id):
    query = text("""
        SELECT COUNT(*) AS book_count
        FROM books
        WHERE store_id = :store_id
    """)

    with engine.connect() as connection:
        book_count = connection.execute(query,{"store_id": store_id}).scalar_one()

    return { "store_id": store_id, "book_count": book_count}

def get_genres():
    query = text("""
        SELECT genre 
        FROM genres
        ORDER BY genre
    """)

    with engine.connect() as connection:
        genres = connection.execute(query).scalars().all()

    return {"genres": genres}

def get_books_by_genre(genre, store_id=None, limit=5):
    query = text("""
        SELECT
            b.source_id,
            b.title,
            b.publisher,
            b.year,
            g.genre,
            b.store_id
        FROM books b
        JOIN genres g ON b.genre_id = g.genre_id
        WHERE LOWER(g.genre) = LOWER(:genre)
        AND (CAST(:store_id AS INTEGER) IS NULL
            OR b.store_id = CAST(:store_id AS INTEGER))
        ORDER BY b.title
        LIMIT :limit
    """)

    with engine.connect() as connection:
        books = connection.execute(
            query,
            {
                "genre": genre,
                "store_id": store_id,
                "limit": limit
            }
        ).mappings().all()

    return {"books": [dict(book) for book in books]}

def count_books_by_genre(genre, store_id=None):
    query = text("""
        SELECT COUNT(*)
        FROM books b
        JOIN genres g ON b.genre_id = g.genre_id
        WHERE LOWER(g.genre) = LOWER(:genre)
        AND (CAST(:store_id AS INTEGER) IS NULL
            OR b.store_id = CAST(:store_id AS INTEGER))
    """)

    with engine.connect() as connection:
        count = connection.execute(
            query,
            {
                "genre": genre,
                "store_id": store_id
            }
        ).scalar_one()

    return {
        "genre": genre,
        "store_id": store_id,
        "count": count
    }

def count_authors():
    query = text("""
        SELECT COUNT(*)
        FROM authors
    """)

    with engine.connect() as connection:
        count = connection.execute(query).scalar_one()

    return {"author_count": count}


def get_authors(search=None, store_id=None, starts_with=False, limit=20):
    query = text("""
        SELECT DISTINCT a.author_name
        FROM authors a
        JOIN book_authors ba ON ba.author_id = a.author_id
        JOIN books b ON b.source_id = ba.book_id
        WHERE (
            CAST(:search AS TEXT) IS NULL
            OR (
                :starts_with = TRUE
                AND LOWER(a.author_name) LIKE LOWER(CAST(:search AS TEXT) || '%')
            )
            OR (
                :starts_with = FALSE
                AND LOWER(a.author_name) LIKE LOWER('%' || CAST(:search AS TEXT) || '%')
            )
        )
        AND (
            CAST(:store_id AS INTEGER) IS NULL
            OR b.store_id = CAST(:store_id AS INTEGER)
        )
        ORDER BY a.author_name
        LIMIT :limit
    """)

    with engine.connect() as connection:
        authors = connection.execute(
            query,
            {
                "search": search,
                "store_id": store_id,
                "starts_with": starts_with,
                "limit": limit
            }
        ).scalars().all()

    return {
        "authors": authors,
        "count": len(authors),
        "limit": limit
    }

def get_books_by_author(author_name, store_id=None, limit=10):
    query = text("""
        SELECT DISTINCT
            b.title,
            a.author_name,
            b.store_id,
            b.publisher,
            b.year
        FROM authors a
        JOIN book_authors ba
            ON ba.author_id = a.author_id
        JOIN books b
            ON b.source_id = ba.book_id
        WHERE LOWER(a.author_name) LIKE LOWER(:author_name)
          AND ( CAST(:store_id AS INTEGER) IS NULL
                OR b.store_id = CAST(:store_id AS INTEGER))
        ORDER BY b.title
        LIMIT :limit
    """)

    with engine.connect() as connection:
        books = connection.execute(
            query,
            {
                "author_name": f"%{author_name}%",
                "store_id": store_id,
                "limit": limit
            }
        ).mappings().all()

    return {
        "books": [dict(book) for book in books],
        "count": len(books),
        "limit": limit
    }

def get_books_by_filter(title=None, publisher=None, year=None, store_id=None, limit=20):
    query = text("""
        SELECT title, publisher, year, store_id
        FROM books
        WHERE (
            CAST(:title AS TEXT) IS NULL
            OR LOWER(title) LIKE LOWER('%' || CAST(:title AS TEXT) || '%')
        )
        AND (
            CAST(:publisher AS TEXT) IS NULL
            OR LOWER(publisher) LIKE LOWER('%' || CAST(:publisher AS TEXT) || '%')
        )
        AND (
            CAST(:year AS INTEGER) IS NULL
            OR year = CAST(:year AS INTEGER)
        )
        AND (
            CAST(:store_id AS INTEGER) IS NULL
            OR store_id = CAST(:store_id AS INTEGER)
        )
        ORDER BY title
        LIMIT :limit
    """)

    with engine.connect() as connection:
        books = connection.execute(
            query,
            {
                "title": title,
                "publisher": publisher,
                "year": year,
                "store_id": store_id,
                "limit": limit
            }
        ).mappings().all()

    return {
        "books": [dict(book) for book in books],
        "count": len(books),
        "limit": limit
    }


def count_books_by_filter(year=None, publisher=None, store_id=None):
    query = text("""
        SELECT COUNT(*)
        FROM books
        WHERE (
            CAST(:year AS INTEGER) IS NULL
            OR year = CAST(:year AS INTEGER)
        )
        AND (
            CAST(:publisher AS TEXT) IS NULL
            OR LOWER(publisher) LIKE
               LOWER('%' || CAST(:publisher AS TEXT) || '%')
        )
        AND (
            CAST(:store_id AS INTEGER) IS NULL
            OR store_id = CAST(:store_id AS INTEGER)
        )
    """)

    with engine.connect() as connection:
        count = connection.execute(
            query,
            {
                "year": year,
                "publisher": publisher,
                "store_id": store_id
            }
        ).scalar_one()

    return {
        "year": year,
        "publisher": publisher,
        "store_id": store_id,
        "count": count
    }

def get_top_spending_users(store_id=None, limit=10):
    query = """
        SELECT
            o.user_id AS source_id,
            o.store_id,
            u.name,
            u.email,
            ROUND(SUM(o.paid_price)::numeric, 2) AS total_spent,
            COUNT(*) AS order_count
        FROM orders o
        JOIN users u
            ON u.source_id = o.user_id
            AND u.store_id = o.store_id
        WHERE 2=2
    """

    params = {}

    if store_id is not None:
        query += " AND o.store_id = :store_id"
        params["store_id"] = store_id

    query += """
        GROUP BY o.user_id, o.store_id, u.name, u.email
        ORDER BY total_spent DESC
        LIMIT :limit
    """

    params["limit"] = max(1, min(int(limit), 100))

    with engine.connect() as connection:
        result = connection.execute(
            text(query), params
        ).mappings().all()

    return [
        {
            **dict(row),
            "total_spent": float(row["total_spent"] or 0)
        }
        for row in result
    ]

def count_users(store_id=None):
    query = text("""
        SELECT COUNT(*)
        FROM users
        WHERE (
            CAST(:store_id AS INTEGER) IS NULL
            OR store_id = CAST(:store_id AS INTEGER)
        )
    """)

    with engine.connect() as connection:
        count = connection.execute(
            query,
            {"store_id": store_id}
        ).scalar_one()

    return {
        "store_id": store_id,
        "user_count": count
    }


def _get_user_filter_patterns(
    name=None,
    email=None,
    phone=None,
    address=None,
    match_mode="contains",
):
    if match_mode not in ("contains", "starts_with", "ends_with"):
        raise ValueError(
            "match_mode must be 'contains', 'starts_with', or 'ends_with'"
        )

    prefix = "%" if match_mode in ("contains", "ends_with") else ""
    suffix = "%" if match_mode in ("contains", "starts_with") else ""

    def make_pattern(value):
        return None if value is None else f"{prefix}{value}{suffix}"

    return {
        "name_pattern": make_pattern(name),
        "email_pattern": make_pattern(email),
        "phone_pattern": make_pattern(phone),
        "address_pattern": make_pattern(address),
    }


def count_users_by_filter(
    name=None,
    email=None,
    phone=None,
    address=None,
    store_id=None,
    match_mode="contains",
):
    patterns = _get_user_filter_patterns(
        name, email, phone, address, match_mode
    )
    query = text("""
        SELECT COUNT(*)
        FROM users
        WHERE (
            CAST(:name_pattern AS TEXT) IS NULL
            OR LOWER(name) LIKE LOWER(CAST(:name_pattern AS TEXT))
        )
        AND (
            CAST(:email_pattern AS TEXT) IS NULL
            OR LOWER(email) LIKE LOWER(CAST(:email_pattern AS TEXT))
        )
        AND (
            CAST(:phone_pattern AS TEXT) IS NULL
            OR phone LIKE CAST(:phone_pattern AS TEXT)
        )
        AND (
            CAST(:address_pattern AS TEXT) IS NULL
            OR LOWER(address) LIKE LOWER(CAST(:address_pattern AS TEXT))
        )
        AND (
            CAST(:store_id AS INTEGER) IS NULL
            OR store_id = CAST(:store_id AS INTEGER)
        )
    """)

    with engine.connect() as connection:
        count = connection.execute(
            query,
            {
                **patterns,
                "store_id": store_id
            }
        ).scalar_one()

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "store_id": store_id,
        "count": count
    }


def get_users_by_filter(
    name=None,
    email=None,
    phone=None,
    address=None,
    store_id=None,
    limit=10,
    match_mode="contains",
):
    patterns = _get_user_filter_patterns(
        name, email, phone, address, match_mode
    )
    query = text("""
        SELECT name, email, phone, address, store_id
        FROM users
        WHERE (
            CAST(:name_pattern AS TEXT) IS NULL
            OR LOWER(name) LIKE LOWER(CAST(:name_pattern AS TEXT))
        )
        AND (
            CAST(:email_pattern AS TEXT) IS NULL
            OR LOWER(email) LIKE LOWER(CAST(:email_pattern AS TEXT))
        )
        AND (
            CAST(:phone_pattern AS TEXT) IS NULL
            OR phone LIKE CAST(:phone_pattern AS TEXT)
        )
        AND (
            CAST(:address_pattern AS TEXT) IS NULL
            OR LOWER(address) LIKE LOWER(CAST(:address_pattern AS TEXT))
        )
        AND (
            CAST(:store_id AS INTEGER) IS NULL
            OR store_id = CAST(:store_id AS INTEGER)
        )
        ORDER BY name
        LIMIT :limit
    """)

    with engine.connect() as connection:
        users = connection.execute(
            query,
            {
                **patterns,
                "store_id": store_id,
                "limit": limit
            }
        ).mappings().all()

    return {
        "users": [dict(user) for user in users],
        "count": len(users),
        "limit": limit
    }



def get_order_summary(store_id=None):
    query = text("""
        SELECT
            COUNT(*) AS order_count,
            COALESCE(SUM(quantity), 0) AS total_quantity,
            COALESCE(SUM(paid_price), 0) AS total_revenue,
            COALESCE(AVG(paid_price), 0) AS average_order_value,
            COALESCE(AVG(unit_price), 0) AS average_unit_price
        FROM orders
    """)

    params = {}

    if store_id is not None:
        query = text("""
            SELECT
                COUNT(*) AS order_count,
                COALESCE(SUM(quantity), 0) AS total_quantity,
                COALESCE(SUM(paid_price), 0) AS total_revenue,
                COALESCE(AVG(paid_price), 0) AS average_order_value,
                COALESCE(AVG(unit_price), 0) AS average_unit_price
            FROM orders
            WHERE store_id = :store_id
        """)
        params["store_id"] = store_id

    with engine.connect() as connection:
        result = connection.execute(
            query, params
        ).mappings().one()

    summary = dict(result)

    for key in (
        "total_revenue",
        "average_order_value",
        "average_unit_price"
    ):
        summary[key] = round(float(summary[key]), 2)

    return {
        "store_id": store_id,
        **summary
    }


def get_orders_by_filter(
    store_id=None,
    user_id=None,
    book_id=None,
    start_date=None,
    end_date=None,
    has_shipping=None,
    limit=10
):
    query = """
        SELECT
            id,
            source_id,
            user_id,
            book_id,
            quantity,
            unit_price,
            timestamp,
            shipping,
            paid_price,
            store_id
        FROM orders
        WHERE 1=1
    """

    params = {}

    if store_id is not None:
        query += " AND store_id = :store_id"
        params["store_id"] = store_id

    if user_id is not None:
        query += " AND user_id = :user_id"
        params["user_id"] = user_id

    if book_id is not None:
        query += " AND book_id = :book_id"
        params["book_id"] = book_id

    if start_date is not None:
        query += " AND timestamp >= :start_date"
        params["start_date"] = start_date

    if end_date is not None:
        query += " AND timestamp < :end_date"
        params["end_date"] = end_date

    if has_shipping is True:
        query += " AND shipping IS NOT NULL AND TRIM(shipping) <> ''"
    elif has_shipping is False:
        query += " AND (shipping IS NULL OR TRIM(shipping) = '')"

    query += " ORDER BY timestamp DESC LIMIT :limit"
    params["limit"] = max(1, min(int(limit), 100))

    with engine.connect() as connection:
        result = connection.execute(
            text(query), params
        ).mappings().all()

    return [dict(row) for row in result]


def get_sales_by_period(
    period="month",
    store_id=None,
    start_date=None,
    end_date=None
):
    if period not in ("day", "month", "year"):
        raise ValueError("Period must be 'day', 'month', or 'year'")

    date_format = {
        "day": "YYYY-MM-DD",
        "month": "YYYY-MM",
        "year": "YYYY"
    }[period]

    query = f"""
        SELECT
            TO_CHAR(DATE_TRUNC('{period}', timestamp), '{date_format}')
                AS period,
            COUNT(*) AS order_count,
            COALESCE(SUM(quantity), 0) AS total_quantity,
            COALESCE(SUM(paid_price), 0) AS total_revenue
        FROM orders
        WHERE timestamp IS NOT NULL
    """

    params = {}

    if store_id is not None:
        query += " AND store_id = :store_id"
        params["store_id"] = store_id

    if start_date is not None:
        query += " AND timestamp >= :start_date"
        params["start_date"] = start_date

    if end_date is not None:
        query += " AND timestamp < :end_date"
        params["end_date"] = end_date

    query += f"""
        GROUP BY DATE_TRUNC('{period}', timestamp)
        ORDER BY DATE_TRUNC('{period}', timestamp)
    """

    with engine.connect() as connection:
        result = connection.execute(
            text(query), params
        ).mappings().all()

    return {
        "period_type": period,
        "store_id": store_id,
        "sales": [
            {
                **dict(row),
                "total_revenue": round(float(row["total_revenue"]), 2)
            }
            for row in result
        ]
    }

def get_top_selling_books(
    store_id=None,
    sort_by="quantity",
    limit=10
):
    if sort_by not in ("quantity", "revenue"):
        raise ValueError("sort_by must be 'quantity' or 'revenue'")

    order_column = (
        "total_quantity" if sort_by == "quantity"
        else "total_revenue"
    )

    query = """
        SELECT
            b.title,
            JSONB_AGG(DISTINCT JSONB_BUILD_OBJECT(
                'source_id', b.source_id,
                'store_id', o.store_id
            )) AS catalog_entries,
            COALESCE(SUM(o.quantity), 0) AS total_quantity,
            ROUND(COALESCE(SUM(o.paid_price), 0)::numeric, 2) AS total_revenue
        FROM orders o
        JOIN books b
            ON b.source_id = o.book_id
            AND b.store_id = o.store_id
        WHERE 2=2
    """

    params = {}

    if store_id is not None:
        query += " AND o.store_id = :store_id"
        params["store_id"] = store_id

    query += f"""
        GROUP BY b.title
        ORDER BY {order_column} DESC, b.title
        LIMIT :limit
    """

    params["limit"] = max(1, min(int(limit), 100))

    with engine.connect() as connection:
        result = connection.execute(text(query), params).mappings().all()

    return [
        {
            **dict(row),
            "total_revenue": float(row["total_revenue"] or 0)
        }
        for row in result]


def get_ordered_book_quantity(
    book_id=None,
    user_id=None,
    store_id=None
):
    query = text("""
        SELECT
            SUM(quantity) AS total_quantity,
            COUNT(*) AS order_count
        FROM orders
        WHERE (
            CAST(:book_id AS INTEGER) IS NULL
            OR book_id = CAST(:book_id AS INTEGER)
        )
        AND (
            CAST(:user_id AS INTEGER) IS NULL
            OR user_id = CAST(:user_id AS INTEGER)
        )
        AND (
            CAST(:store_id AS INTEGER) IS NULL
            OR store_id = CAST(:store_id AS INTEGER)
        )
    """)

    params = {
        "book_id": book_id,
        "user_id": user_id,
        "store_id": store_id
    }

    with engine.connect() as connection:
        result = connection.execute(
            query, params
        ).mappings().one()

    return {
        "book_id": book_id,
        "user_id": user_id,
        "store_id": store_id,
        "total_quantity": result["total_quantity"] or 0,
        "order_count": result["order_count"]
    }


def control_dashboard(
    store_id=None,
    top_days=None,
    start_date=None,
    end_date=None,
    granularity=None,
    clear_date_range=False,
    reset_defaults=False,
):
    if reset_defaults:
        st.session_state["pending_dashboard_store_id"] = 1
        st.session_state["dashboard_top_days"] = 5
        st.session_state["pending_dashboard_settings"] = {
            "dashboard_start_date": None,
            "dashboard_end_date": None,
            "dashboard_granularity": "day",
        }
        st.session_state["dashboard_update_pending"] = True
        return {
            "success": True,
            "message": "Dashboard settings reset to defaults.",
            "store_id": 1,
            "top_days": 5,
            "start_date": None,
            "end_date": None,
            "granularity": "day",
        }

    if store_id is not None:
        if store_id not in [1, 2, 3, 4, 5]:
            return {"success": False, "error": "Invalid store ID"}

    if top_days is not None:
        if not 1 <= top_days <= 10:
            return {
                "success": False,
                "error": "top_days must be between 1 and 10"
            }

    if granularity is not None and granularity not in ["day", "week", "month"]:
        return {
            "success": False,
            "error": "granularity must be day, week, or month"
        }

    current_start_date = st.session_state.get("dashboard_start_date")
    current_end_date = st.session_state.get("dashboard_end_date")
    try:
        new_start_date = (
            None if clear_date_range else
            date.fromisoformat(start_date) if start_date is not None else
            current_start_date
        )
        new_end_date = (
            None if clear_date_range else
            date.fromisoformat(end_date) if end_date is not None else
            current_end_date
        )
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "Dates must use YYYY-MM-DD format"
        }

    if (
        new_start_date is not None
        and new_end_date is not None
        and new_start_date > new_end_date
    ):
        return {
            "success": False,
            "error": "start_date must be on or before end_date"
        }

    if store_id is not None:
        st.session_state["pending_dashboard_store_id"] = store_id

    if top_days is not None:
        st.session_state["dashboard_top_days"] = top_days

    pending_settings = {}
    if start_date is not None or clear_date_range:
        pending_settings["dashboard_start_date"] = new_start_date
    if end_date is not None or clear_date_range:
        pending_settings["dashboard_end_date"] = new_end_date
    if granularity is not None:
        pending_settings["dashboard_granularity"] = granularity
    if pending_settings:
        st.session_state["pending_dashboard_settings"] = pending_settings

    st.session_state["dashboard_update_pending"] = True

    return {
        "success": True,
        "message": "Dashboard settings updated.",
        "store_id": store_id if store_id is not None else st.session_state.get("dashboard_store_selector", 1),
        "top_days": st.session_state.get("dashboard_top_days", 5),
        "start_date": new_start_date.isoformat() if new_start_date else None,
        "end_date": new_end_date.isoformat() if new_end_date else None,
        "granularity": granularity or st.session_state.get("dashboard_granularity", "day"),
    }
