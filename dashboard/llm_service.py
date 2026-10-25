import os
import db_tools
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("LLM_KEY"))
MODEL = "gemini-3.5-flash-lite"

TOOL_FUNCTIONS = {
    "get_book_count": db_tools.get_book_count,
    "get_genres": db_tools.get_genres,
    "get_books_by_genre": db_tools.get_books_by_genre,
    "count_books_by_genre": db_tools.count_books_by_genre,
    "count_authors": db_tools.count_authors,
    "get_authors": db_tools.get_authors,
    "get_books_by_author": db_tools.get_books_by_author,
    "get_books_by_filter": db_tools.get_books_by_filter,
    "count_books_by_filter": db_tools.count_books_by_filter,
    "count_users": db_tools.count_users,
    "count_users_by_filter": db_tools.count_users_by_filter,
    "get_users_by_filter": db_tools.get_users_by_filter,
    "get_top_spending_users": db_tools.get_top_spending_users,
    "get_order_summary": db_tools.get_order_summary,
    "get_orders_by_filter": db_tools.get_orders_by_filter,
    "get_sales_by_period":db_tools.get_sales_by_period,
    "get_top_selling_books":db_tools.get_top_selling_books,
    "get_ordered_book_quantity": db_tools.get_ordered_book_quantity,
    "control_dashboard":db_tools.control_dashboard,
}

def create_tool(tools, name, description, parameters, required=None):
    tools.append(
        types.FunctionDeclaration(
            name=name,
            description=description,
            parameters_json_schema={
                "type": "object",
                "properties": parameters,
                "required": required or []
            }
        )
    )

def create_chat():

    tools = []

    create_tool(
        tools= tools,
        name="get_book_count",
        description="Get the number of books in a specific store.",
        parameters={
            "store_id": {
                "type": "integer",
                "description": "Store ID, from 1 to 5."
            }})
    
    create_tool(
            tools= tools,
            name="get_genres",
            description="Get the available book genres across the stores.",
            parameters={})

    create_tool(
        tools= tools,
        name="get_books_by_genre",
        description=(
            "Find books belonging to a specific genre."
            "Can optionally filter by store and limit the number of results."
            "Use get_genres to check which genres are available if needed."
            ),
        parameters={
            "genre": {
                "type": "string",
                "description": "The book genre to search for, matching an available genre."
            },
            "store_id": {
                "type": ["integer", "null"],
                "description": "Optional store ID, from 1 to 5. Use null to search all stores."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of books to return. Defaults to 5."
                }})
    
    create_tool(
        tools=tools,
        name="count_books_by_genre",
        description=(
            "Count the number of books belonging to a specific genre, "
            "Can optionally filter by store."
        ),
        parameters={
            "genre": {
                "type": "string",
                "description": "The book genre to count."
            },
            "store_id": {
                "type": ["integer", "null"],
                "description": "Store ID from 1 to 5. Use null for all stores."
            }
        },
        required=["genre"]
    )

    create_tool(
        tools=tools,
        name="count_authors",
        description="Count the total number of authors in the database.",
        parameters={}
    )

    create_tool(
        tools=tools,
        name="get_authors",
        description=(
            "Retrieve authors from the database."
            "Can filter authors by store, search author names or find authors whose name starts with a given text."
            "Use this tool to check whether an author exists or to list authors matching the user's request."
        ),
        parameters={
            "search": {
                "type": ["string", "null"],
                "description": "Author name or text to search for. Use null for no name filter."
            },
            "store_id": {
                "type": ["integer", "null"],
                "description": "Store ID from 1 to 5. Use null to search across all stores."
            },
            "starts_with": {
                "type": "boolean",
                "description": "True to match names starting with search; false to match names containing search."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of authors to return. Default 10."
            }
        })

    
    create_tool(
        tools=tools,
        name="get_books_by_author",
        description=(
            "Find books written by an author."
            "Use this tool when asked which books an author wrote or whether books by an author exist."
            "Optionally filter by store."
        ),
        parameters={
            "author_name": {
                "type": "string",
                "description": "The author's name or part of their name."
            },
            "store_id": {
                "type": ["integer", "null"],
                "description": "Store ID from 1 to 5, or null for all stores."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of books to return."
            }
        },
        required=["author_name"]
    )

    
    create_tool(
        tools=tools,
        name="get_books_by_filter",
        description=(
            "Search for books by publisher, publication year, title, or a combination of them."
            "Optionally filter by store."
            "Use this tool when the user asks which books were published by a publisher, in a specific year, or by a publisher in a year, or by a title."
            "Leave unspecified filters null."
        ),
        parameters={
            "title": {
                    "type": ["string", "null"],
                    "description": "The book title or part of the title to search for. Use null if unspecified."
            },
            "publisher": {
                "type": ["string", "null"],
                "description": "Publisher name or part of the name, or null if unspecified."
            },
            "year": {
                "type": ["integer", "null"],
                "description": "Exact publication year, or null if unspecified."
            },
            "store_id": {
                "type": ["integer", "null"],
                "description": "Store ID from 1 to 5, or null if unspecified."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of books to return."
            }
        },
        required=[]
    )

    create_tool(
        tools=tools,
        name="count_books_by_filter",
        description=(
            "Count books matching optional filters. "
            "Use year to filter by publication year, publisher to filter by publisher name or part of the name, and store_id to filter by store. "
            "Multiple filters can be combined. "
            "Returns the exact number of matching books."
        ),
        parameters={
            "year": {
                "type": "integer",
                "description": "Exact publication year."
            },
            "publisher": {
                "type": "string",
                "description": "Publisher name or part of the name."
            },
            "store_id": {
                "type": "integer",
                "description": "Store ID from 1 to 5."
            }
        },
        required=[]
    )
  
    create_tool(
        tools=tools,
        name="count_users",
        description=(
            "Count user records in the database. "
            "Optionally filter by store_id. "
            "If store_id is unspecified, count users across all stores."
        ),
        parameters={
            "store_id": {
                "type": "integer",
                "description": "Store ID from 1 to 5."
            }
        },
        required=[]
    )

    create_tool(
        tools=tools,
        name="count_users_by_filter",
        description=(
            "Count user records matching optional filters by name, email, phone, address, or store. "
            "Multiple filters can be combined. "
            "Use match_mode='contains' (default), 'starts_with', or 'ends_with' to control where each text filter matches. "
            "Returns the exact number of matching records."
        ),
        parameters={
            "name": {
                "type": "string",
                "description": "Full or partial user name."
            },
            "email": {
                "type": "string",
                "description": "Full or partial email."
            },
            "phone": {
                "type": "string",
                "description": "Full or partial phone number."
            },
            "address": {
                "type": "string",
                "description": "Full or partial address."
            },
            "store_id": {
                "type": "integer",
                "description": "Store ID from 1 to 5."
            },
            "match_mode": {
                "type": "string",
                "enum": ["contains", "starts_with", "ends_with"],
                "description": (
                    "How each provided text filter matches: contains anywhere, "
                    "starts_with at the beginning, or ends_with at the end. "
                    "Defaults to contains."
                )
            }
        },
        required=[]
    )

    create_tool(
        tools=tools,
        name="get_users_by_filter",
        description=(
            "Retrieve user records matching optional filters by name, email, phone, address, or store."
            "Multiple filters can be combined. "
            "Use match_mode='contains' (default), 'starts_with', or 'ends_with' to control where each text filter matches. "
            "Returns up to the requested limit. Use count_users_by_filter for exact counts."
        ),
        parameters={
            "name": {
                "type": "string",
                "description": "Full or partial user name."
            },
            "email": {
                "type": "string",
                "description": "Full or partial email."
            },
            "phone": {
                "type": "string",
                "description": "Full or partial phone number."
            },
            "address": {
                "type": "string",
                "description": "Full or partial address."
            },
            "store_id": {
                "type": "integer",
                "description": "Store ID from 1 to 5."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of records to return."
            },
            "match_mode": {
                "type": "string",
                "enum": ["contains", "starts_with", "ends_with"],
                "description": (
                    "How each provided text filter matches: contains anywhere, "
                    "starts_with at the beginning, or ends_with at the end. "
                    "Defaults to contains."
                )
            }
        },
        required=[]
    )

    create_tool(
        tools=tools,
        name="get_order_summary",
        description=(
            "Get order statistics for all stores or one specific store. "
            "Returns the number of order records, total quantity, total revenue based on paid_price, average order-record value and average unit price. "
            "Use store_id to filter by store."
        ),
        parameters={
            "store_id": {
                "type": "integer",
                "description": "Store ID, from 1 to 5."
            }
        },
        required=[]
    )
 
    create_tool(
        tools=tools,
        name="get_orders_by_filter",
        description=(
            "Retrieve a limited list of orders using optional filters. "
            "Filters can include store_id, user_id, book_id, start_date, end_date, and whether a shipping address exists. "
            "Dates should use YYYY-MM-DD format. "
            "Results are ordered by timestamp, newest first. "
            "Use this tool when the user asks to find, list, or inspect orders."
        ),
        parameters={
            "store_id": {
                "type": "integer",
                "description": "Store ID, from 1 to 5."
            },
            "user_id": {
                "type": "integer",
                "description": "Original user source ID stored in orders."
            },
            "book_id": {
                "type": "integer",
                "description": "Original book source ID stored in orders."
            },
            "start_date": {
                "type": "string",
                "description": "Inclusive start date, YYYY-MM-DD."
            },
            "end_date": {
                "type": "string",
                "description": "Exclusive end date, YYYY-MM-DD."
            },
            "has_shipping": {
                "type": "boolean",
                "description": (
                    "True for orders with a shipping address, "
                    "false for orders without one."
                )
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results, from 1 to 100. Default is 10."
            }
        },
        required=[]
    )
 
    create_tool(
        tools=tools,
        name="get_sales_by_period",
        description=(
            "Aggregate sales by day, month, or year. "
            "Returns order-record count, total quantity sold, and total revenue based on paid_price for each period. "
            "Optional filters include store_id, start_date, and end_date. "
            "Dates must use YYYY-MM-DD format. "
            "The end_date is exclusive. "
            "Use this tool for sales trends and revenue comparisons over time."
        ),
        parameters={
            "period": {
                "type": "string",
                "enum": ["day", "month", "year"],
                "description": "Time grouping: day, month, or year."
            },
            "store_id": {
                "type": "integer",
                "description": "Optional store ID, from 1 to 5."
            },
            "start_date": {
                "type": "string",
                "description": "Optional inclusive start date, YYYY-MM-DD."
            },
            "end_date": {
                "type": "string",
                "description": "Optional exclusive end date, YYYY-MM-DD."
            }
        },
        required=[]
    )

    
    create_tool(
        tools=tools,
        name="get_top_selling_books",
        description=(
            "Find the best-selling books based on total quantity sold or total revenue. Optionally filter by store_id. "
            "Use sort_by='quantity' for most copies sold or sort_by='revenue' for highest revenue. "
            "Without store_id, combine sales for matching book titles across all stores. "
            "Returns title, catalog_entries (source ID and store ID pairs), total quantity, and total revenue. "
            "Limit results to at most 100 books."
        ),
        parameters={
            "store_id": {
                "type": "integer",
                "description": "Optional store ID, from 1 to 5."
            },
            "sort_by": {
                "type": "string",
                "enum": ["quantity", "revenue"],
                "description": "Rank by quantity sold or total revenue."
            },
            "limit": {
                "type": "integer",
                "description": "Number of books to return, from 1 to 100."
            }
        },
        required=[]
    )

    create_tool(
        tools=tools,
        name="get_ordered_book_quantity",
        description=(
            "Sum ordered copies and count matching orders, optionally filtered by book_id (books.source_id), user_id, and store_id. "
            "This reports orders, not current stock. "
            "For a book title, look up its source_id and store_id first; IDs may differ across stores. "
            "Compare stores by calling this tool separately for each one."
        ),
        parameters={
            "book_id": {"type": "integer", "description": "Book source_id"},
            "user_id": {"type": "integer", "description": "User source_id"},
            "store_id": {"type": "integer", "description": "Store ID (1-5)"}
        }
    )

    create_tool(
        tools=tools,
        name="get_top_spending_users",
        description=(
            "Rank users by total spending (sum of order paid_price). "
            "Returns name, email, store_id, total_spent, and order_count. "
            "Optionally filter by store_id; users are distinguished by source_id and store_id."
        ),
        parameters={
            "store_id": {
                "type": "integer",
                "description": "Optional store ID (1-5). Omit for all stores."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of users to return (1-100). Defaults to 10."
            }
        }
    )

    
    
    create_tool(
        tools=tools,
        name="control_dashboard",
        description=(
            "Update the dashboard when asked. Change only the requested settings: store (1-5), "
            "top revenue periods (1-10), inclusive date range, or chart interval (day/week/month). "
            "Use clear_date_range to remove date limits. Use reset_defaults to restore store 1, "
            "top 5, all dates, and daily interval; do not combine it with other changes."
        ),
        parameters={
            "store_id": {
                "type": ["integer", "null"],
                "description": "Store ID from 1 to 5. Null if not requested."
            },
            "top_days": {
                "type": ["integer", "null"],
                "description": (
                    "Number of top revenue periods to display, from 1 to 10. "
                    "Null if not requested."
                )
            },
            "start_date": {
                "type": ["string", "null"],
                "description": "Optional inclusive start date, YYYY-MM-DD."
            },
            "end_date": {
                "type": ["string", "null"],
                "description": "Optional inclusive end date, YYYY-MM-DD."
            },
            "granularity": {
                "type": ["string", "null"],
                "enum": ["day", "week", "month"],
                "description": "Revenue chart grouping interval."
            },
            "clear_date_range": {
                "type": "boolean",
                "description": "Set true to remove both date limits."
            },
            "reset_defaults": {
                "type": "boolean",
                "description": (
                    "Set true to reset all dashboard settings to defaults: store 1, "
                    "top 5 periods, all dates, and daily grouping."
                )
            }
        }
    )

    tool = types.Tool(function_declarations=tools)

    return client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an AI assistant for a bookstore dashboard."
                "Use available tools whenever database information is needed."
                "Never invent database results."
                "If a tool cannot answer a question, explain the limitation."
                "Treat tool results as the only source of truth for database facts."
                "When reporting a number returned by a tool, reproduce it exactly."
                "Never estimate, replace, or invent database values."
                "Do not show internal database IDs to users."
                "There are only five stores, numbered from 1 to 5."
                "Answer the user's question directly and concisely."
                "Provide additional breakdowns only when they are useful or explicitly requested."
                "When the user explicitly asks to change dashboard settings, use control_dashboard. "
                "Dashboard revenue chart intervals are day, week, or month; its optional start and end dates are inclusive. "
                "Do not claim a change was made unless the tool returns success. "
                "After a successful change, tell the user they can see the changes in the Dashboard tab."
                "Prefer human-readable values, such as names and titles, over IDs when answering users."
                "Do not ask users for IDs or expose them in responses unless explicitly requested."
                "Use IDs internally when necessary to identify records or join related data."
                "Never guess IDs, retrieve them from the database when needed."
            ),
            tools=[tool]
        )
    )

def send_message(chat, question):
    response = chat.send_message(question)

    while response.function_calls:
        function_responses = []

        for function_call in response.function_calls:
            function = TOOL_FUNCTIONS.get(function_call.name)

            if function is None:
                result = {"error": "Unknown function"}
            else:
                result = function(**function_call.args)

            print("DATABASE RESULT:", result)

            function_responses.append(
                types.Part.from_function_response(
                    name=function_call.name,
                    response={
                        "result": result,
                        "instruction": (
                            "Use this result as the source of truth. "
                            "If no matching records were found, say so clearly. "
                            "Do not invent database results."
                        )}
                ))

        response = chat.send_message(function_responses)

    return response.text or "I couldn't generate a response"
