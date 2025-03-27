"""
Text2SQL Streamlit UI

A web interface for the Text2SQL application, allowing users to:
1. Connect to a PostgreSQL database
2. Enter natural language queries
3. View the generated SQL and results
"""

import os
import streamlit as st
import pandas as pd
from loguru import logger

# Import our application components
from utils.db_connection import DatabaseConnection
from metastore.metastore import MetaStore
# TODO: Import the actual query processing pipeline once it's implemented

# Page configuration
st.set_page_config(
    page_title="Text2SQL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for persistence
if "db_connection" not in st.session_state:
    st.session_state.db_connection = None
if "connected" not in st.session_state:
    st.session_state.connected = False
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "metastore_loaded" not in st.session_state:
    st.session_state.metastore_loaded = False


def connect_to_db(connection_string):
    """Establish database connection"""
    db_conn = DatabaseConnection(connection_string)
    success = db_conn.connect()
    if success:
        st.session_state.db_connection = db_conn
        st.session_state.connected = True
        return True, "Successfully connected to database"
    return False, "Failed to connect to database"


def load_metastore():
    """Load the metastore with database schema information"""
    try:
        # Paths relative to project root
        vector_db_path = os.path.join("metastore", "vector_db")
        schema_dir = os.path.join("metastore", "db_metadata")
        table_heads_dir = os.path.join("metastore", "table_heads")
        sql_pairs_dir = os.path.join("metastore", "sql_pairs")
        
        # Initialize metastore
        metastore = MetaStore(
            vector_db_path=vector_db_path,
            schema_dir=schema_dir,
            table_heads_dir=table_heads_dir,
            sql_pairs_dir=sql_pairs_dir
        )
        
        # If we have a database connection, extract and save the schema
        if st.session_state.connected:
            schema_info = st.session_state.db_connection.get_schema_info()
            # TODO: Implement the schema extraction and saving logic
            # This would involve writing schema_info to the appropriate files
            # and generating embeddings
            
        st.session_state.metastore_loaded = True
        return True, "Successfully loaded metastore"
    except Exception as e:
        logger.error(f"Error loading metastore: {str(e)}")
        return False, f"Error loading metastore: {str(e)}"


def process_nl_query(nl_query):
    """Process natural language query to SQL"""
    # This is a placeholder. In a real implementation, this would:
    # 1. Use the Query Agent to decompose the query
    # 2. Use the Context Agent to enrich with database context
    # 3. Use the Schema Agent to generate the final SQL
    
    # For now, return a dummy SQL query based on the input
    # TODO: Replace with actual implementation
    dummy_sql = f"SELECT * FROM users WHERE description LIKE '%{nl_query}%' LIMIT 10;"
    return dummy_sql


def main():
    """Main function to render the Streamlit UI"""
    st.title("Text2SQL: Natural Language to SQL Query Converter")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Database Connection")
        
        # Database connection form
        with st.form("db_connection_form"):
            host = st.text_input("Host", "localhost")
            port = st.text_input("Port", "5432")
            database = st.text_input("Database", "postgres")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            conn_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            submit_button = st.form_submit_button(label="Connect")
            
            if submit_button:
                success, message = connect_to_db(conn_str)
                if success:
                    st.success(message)
                    # Try to load metastore after successful connection
                    metastore_success, metastore_msg = load_metastore()
                    if metastore_success:
                        st.success(metastore_msg)
                    else:
                        st.error(metastore_msg)
                else:
                    st.error(message)
        
        # Display connection status
        if st.session_state.connected:
            st.success("✅ Connected to database")
            
            # Display tables in the database
            if st.session_state.db_connection:
                tables = st.session_state.db_connection.get_tables()
                if tables:
                    st.subheader("Available Tables")
                    for table in tables:
                        st.write(f"- {table}")
                else:
                    st.info("No tables found in database")
        else:
            st.error("❌ Not connected to database")
    
    # Main area for query input and results
    if st.session_state.connected:
        # Natural language query input
        st.header("Convert Natural Language to SQL")
        nl_query = st.text_area("Enter your question in natural language", 
                                height=100, 
                                placeholder="e.g., Show me all customers from New York who made a purchase last month")
        
        if st.button("Generate SQL"):
            if nl_query:
                with st.spinner("Generating SQL..."):
                    # Process the query
                    generated_sql = process_nl_query(nl_query)
                    
                    # Store in history
                    st.session_state.query_history.append({
                        "natural_language": nl_query,
                        "sql": generated_sql,
                        "results": None  # Will be populated if executed
                    })
            else:
                st.warning("Please enter a query first")
        
        # Display query history and results
        if st.session_state.query_history:
            st.header("Query Results")
            
            # Get the most recent query
            latest_query = st.session_state.query_history[-1]
            
            # Display the generated SQL
            st.subheader("Generated SQL")
            st.code(latest_query["sql"], language="sql")
            
            # Execute the query
            if st.button("Execute SQL"):
                with st.spinner("Executing query..."):
                    success, results = st.session_state.db_connection.execute_query(latest_query["sql"])
                    
                    # Store results in history
                    latest_query["results"] = results if success else {"error": results}
                    
                    if success:
                        if "rows" in results:
                            st.subheader("Query Results")
                            # Convert to DataFrame for display
                            df = pd.DataFrame(results["rows"], columns=results["columns"])
                            st.dataframe(df)
                        else:
                            st.success(results["message"])
                    else:
                        st.error(f"Error executing query: {results}")
    else:
        # Not connected to database
        st.info("Please connect to a database using the sidebar form first.")


if __name__ == "__main__":
    main()