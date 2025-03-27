"""
Database connection utility for the Text2SQL application.
Handles PostgreSQL connections using SQLAlchemy.
"""

import os
from typing import Dict, Optional, Any
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger


class DatabaseConnection:
    """Manages database connections for the Text2SQL application."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the database connection.
        
        Args:
            connection_string: SQLAlchemy connection string. If None, will try to read from environment.
        """
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self.engine: Optional[Engine] = None
        self.metadata: Optional[MetaData] = None
        self.inspector = None
    
    def connect(self) -> bool:
        """
        Establish connection to the database.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        if not self.connection_string:
            logger.error("No connection string provided")
            return False
        
        try:
            self.engine = create_engine(self.connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            self.inspector = inspect(self.engine)
            
            logger.info(f"Successfully connected to database")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {str(e)}")
            return False
    
    def get_tables(self) -> list:
        """
        Get list of tables in the database.
        
        Returns:
            list: List of table names
        """
        if not self.engine or not self.inspector:
            logger.error("Not connected to database")
            return []
            
        return self.inspector.get_table_names()
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get comprehensive schema information for all tables.
        
        Returns:
            Dict[str, Any]: Dictionary containing table schemas
        """
        if not self.engine or not self.inspector:
            logger.error("Not connected to database")
            return {}
        
        schema_info = {}
        for table_name in self.get_tables():
            columns = self.inspector.get_columns(table_name)
            primary_keys = self.inspector.get_pk_constraint(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            schema_info[table_name] = {
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }
        
        return schema_info
    
    def execute_query(self, query: str) -> tuple:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string to execute
            
        Returns:
            tuple: (success, results or error message)
        """
        if not self.engine:
            return False, "Not connected to database"
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sa.text(query))
                if result.returns_rows:
                    columns = result.keys()
                    rows = result.fetchall()
                    return True, {"columns": columns, "rows": rows}
                return True, {"message": "Query executed successfully"}
                
        except SQLAlchemyError as e:
            logger.error(f"Query execution error: {str(e)}")
            return False, str(e)