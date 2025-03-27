"""
Database schema extraction utility.

This module extracts schema information from a PostgreSQL database
and prepares it for use in the MetaStore vector search system.
"""

import os
import json
from pathlib import Path
import pandas as pd
from typing import Dict, Any, Optional, List
from loguru import logger

from utils.db_connection import DatabaseConnection


def extract_schema(db_connection: DatabaseConnection, output_dir: str):
    """
    Extract database schema information and save it to the specified directory.
    
    Args:
        db_connection: Connected DatabaseConnection instance
        output_dir: Directory to save schema files
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not db_connection or not db_connection.engine:
        logger.error("Database connection not established")
        return False
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        schema_info = db_connection.get_schema_info()
        
        # Save the complete schema information
        with open(os.path.join(output_dir, "complete_schema.json"), "w") as f:
            json.dump(schema_info, f, indent=2, default=str)
        
        # Create individual table schema files for better search granularity
        for table_name, table_info in schema_info.items():
            table_schema = {
                "table_name": table_name,
                "columns": [],
                "primary_keys": table_info["primary_keys"].get("constrained_columns", []),
                "foreign_keys": []
            }
            
            # Process columns
            for col in table_info["columns"]:
                column_data = {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": str(col.get("default", ""))
                }
                table_schema["columns"].append(column_data)
            
            # Process foreign keys
            for fk in table_info["foreign_keys"]:
                fk_data = {
                    "constrained_columns": fk.get("constrained_columns", []),
                    "referred_table": fk.get("referred_table", ""),
                    "referred_columns": fk.get("referred_columns", [])
                }
                table_schema["foreign_keys"].append(fk_data)
            
            # Save individual table schema
            with open(os.path.join(output_dir, f"{table_name}_schema.json"), "w") as f:
                json.dump(table_schema, f, indent=2)
        
        logger.info(f"Successfully extracted schema for {len(schema_info)} tables")
        return True
        
    except Exception as e:
        logger.error(f"Error extracting schema: {str(e)}")
        return False


def extract_table_samples(db_connection: DatabaseConnection, output_dir: str, 
                        sample_size: int = 5):
    """
    Extract sample rows from each table to help with context.
    
    Args:
        db_connection: Connected DatabaseConnection instance
        output_dir: Directory to save sample files
        sample_size: Number of sample rows to extract per table
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not db_connection or not db_connection.engine:
        logger.error("Database connection not established")
        return False
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        tables = db_connection.get_tables()
        
        for table_name in tables:
            query = f"SELECT * FROM {table_name} LIMIT {sample_size}"
            success, results = db_connection.execute_query(query)
            
            if success and "rows" in results:
                # Convert to pandas DataFrame for easier manipulation
                df = pd.DataFrame(results["rows"], columns=results["columns"])
                
                # Save as JSON and CSV for flexibility
                df.to_json(os.path.join(output_dir, f"{table_name}_samples.json"), orient="records", indent=2)
                df.to_csv(os.path.join(output_dir, f"{table_name}_samples.csv"), index=False)
        
        logger.info(f"Successfully extracted samples for {len(tables)} tables")
        return True
        
    except Exception as e:
        logger.error(f"Error extracting table samples: {str(e)}")
        return False


if __name__ == "__main__":
    # Example usage
    conn_str = "postgresql://username:password@localhost:5432/dbname"
    db_conn = DatabaseConnection(conn_str)
    
    if db_conn.connect():
        extract_schema(db_conn, "metastore/db_metadata")
        extract_table_samples(db_conn, "metastore/table_heads")
    else:
        logger.error("Failed to connect to database")