"""
Context Agent - Schema Mapper

This module contains the SchemaMapper class which is responsible for 
mapping natural language entities to database schema elements using vector similarity.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

# Assuming this will be created in the project
from text2sql.metastore.metastore import MetaStore

logger = logging.getLogger(__name__)

class SchemaMapper:
    """
    The SchemaMapper maps natural language entities to database schema elements
    using vector similarity search and sample data matching.
    """
    
    def __init__(self, metastore: MetaStore):
        """
        Initialize the SchemaMapper with a MetaStore instance.
        
        Args:
            metastore: An instance of MetaStore for retrieving database metadata
        """
        self.metastore = metastore
    
    def map_entity_to_column(self, entity_type: str, entity_value: str, 
                            table_name: str) -> Tuple[str, float]:
        """
        Map an entity to a database column using vector similarity search.
        
        Args:
            entity_type: The type of entity (e.g., 'status', 'priority')
            entity_value: The value of the entity (e.g., 'open', 'high')
            table_name: The target table name
            
        Returns:
            A tuple containing the column name and confidence score
        """
        logger.info(f"Mapping entity {entity_type}:{entity_value} to a column in {table_name}")
        
        # Step 1: Try direct mapping from column metadata
        column_match = self._search_column_metadata(entity_type, entity_value, table_name)
        if column_match and column_match[1] > 0.7:  # High confidence threshold
            return column_match
        
        # Step 2: Try using sample data (table heads)
        sample_match = self._search_table_heads(entity_value, table_name)
        if sample_match and sample_match[1] > 0.8:  # Higher threshold for exact value matches
            return sample_match
        
        # Step 3: Try using similar SQL pairs
        sql_pair_match = self._search_sql_pairs(entity_type, entity_value, table_name)
        if sql_pair_match:
            return sql_pair_match
        
        # Step 4: If we have some match from metadata, use it even with lower confidence
        if column_match:
            return column_match
        
        # Step 5: Last resort - heuristic match based on name patterns
        heuristic_match = self._heuristic_match(entity_type, table_name)
        if heuristic_match:
            return heuristic_match
        
        # If all attempts fail, raise an exception
        raise ValueError(f"Could not map entity {entity_type}:{entity_value} to a column in {table_name}")
    
    def _search_column_metadata(self, entity_type: str, entity_value: str, 
                               table_name: str) -> Optional[Tuple[str, float]]:
        """
        Search column metadata for matching columns using vector similarity.
        
        Args:
            entity_type: The type of entity
            entity_value: The value of the entity
            table_name: The target table name
            
        Returns:
            A tuple of (column_name, confidence_score) if found, None otherwise
        """
        # Create a rich query combining entity type and value
        query = f"{entity_type} {entity_value}"
        
        # Search in column metadata with table filter
        columns = self.metastore.search_schema(
            query, 
            filter={"table": table_name}, 
            top_k=3
        )
        
        if columns and len(columns) > 0:
            # Return the highest scoring column with its confidence score
            return columns[0]["name"], columns[0].get("score", 0.0)
        
        return None
    
    def _search_table_heads(self, entity_value: str, 
                           table_name: str) -> Optional[Tuple[str, float]]:
        """
        Search table head samples for matching values.
        
        Args:
            entity_value: The value to search for
            table_name: The target table name
            
        Returns:
            A tuple of (column_name, confidence_score) if found, None otherwise
        """
        # Search for the entity value in sample data
        sample_matches = self.metastore.search_table_heads(
            entity_value, 
            table_name=table_name, 
            top_k=3
        )
        
        if sample_matches and len(sample_matches) > 0:
            # Return the column with the highest confidence of containing the value
            return sample_matches[0]["column_name"], sample_matches[0].get("score", 0.0)
        
        return None
    
    def _search_sql_pairs(self, entity_type: str, entity_value: str, 
                         table_name: str) -> Optional[Tuple[str, float]]:
        """
        Search SQL pairs for similar entities and their mapped columns.
        
        Args:
            entity_type: The type of entity
            entity_value: The value of the entity
            table_name: The target table name
            
        Returns:
            A tuple of (column_name, confidence_score) if found, None otherwise
        """
        # Create a rich query combining entity type, value, and table
        query = f"{entity_type} {entity_value} in {table_name}"
        
        # Search for similar SQL pairs
        similar_pairs = self.metastore.find_similar_sql_pairs(query, top_k=3)
        
        if not similar_pairs:
            return None
        
        # Extract column mappings from similar SQL pairs
        for pair in similar_pairs:
            # This would require SQL parsing or structured annotations in the pairs
            # Simplified implementation - assume pairs have metadata about entity mappings
            mappings = pair.get("entity_mappings", {})
            
            for mapping in mappings:
                if (mapping.get("entity_type") == entity_type and 
                    mapping.get("table") == table_name):
                    return mapping.get("column"), mapping.get("confidence", 0.7)
        
        return None
    
    def _heuristic_match(self, entity_type: str, table_name: str) -> Optional[Tuple[str, float]]:
        """
        Use heuristics to match entity types to columns based on naming conventions.
        
        Args:
            entity_type: The type of entity
            table_name: The target table name
            
        Returns:
            A tuple of (column_name, confidence_score) if found, None otherwise
        """
        # Get all columns for the table
        table_metadata = self.metastore.get_table_metadata(table_name)
        
        if not table_metadata:
            return None
        
        # Map of common entity types to likely column name patterns
        pattern_map = {
            "status": ["status", "state"],
            "priority": ["priority", "importance", "urgency"],
            "category": ["category", "type", "class"],
            "date": ["date", "time", "created", "updated"],
            "id": ["id", "identifier", "key"],
            "name": ["name", "title"],
            "description": ["description", "details", "text"]
        }
        
        # Get patterns for this entity type
        patterns = pattern_map.get(entity_type.lower(), [entity_type.lower()])
        
        # Look for columns matching the patterns
        for column in table_metadata.get("columns", []):
            column_name = column.get("name", "").lower()
            
            for pattern in patterns:
                if pattern in column_name:
                    # Return with a lower confidence score since this is heuristic
                    return column["name"], 0.6
        
        return None
    
    def find_date_column(self, table_name: str) -> Optional[str]:
        """
        Find a date column in the specified table for temporal filtering.
        
        Args:
            table_name: The name of the table
            
        Returns:
            The name of the date column, or None if not found
        """
        # Get the table metadata
        table_metadata = self.metastore.get_table_metadata(table_name)
        
        if not table_metadata:
            return None
        
        # Look for date/time columns based on data type
        for column in table_metadata.get("columns", []):
            data_type = column.get("data_type", "").upper()
            if any(dt in data_type for dt in ["DATE", "TIME", "TIMESTAMP"]):
                return column["name"]
        
        # If no date types found, look for columns with date-related names
        date_patterns = ["date", "time", "created", "updated", "timestamp"]
        for column in table_metadata.get("columns", []):
            column_name = column.get("name", "").lower()
            if any(pattern in column_name for pattern in date_patterns):
                return column["name"]
        
        return None
    
    def get_relevant_columns(self, table_name: str, expected_output: str) -> List[Dict[str, Any]]:
        """
        Find columns relevant to the expected output description.
        
        Args:
            table_name: The target table name
            expected_output: Description of the expected output
            
        Returns:
            A list of relevant column metadata
        """
        # Get all columns for the table
        table_metadata = self.metastore.get_table_metadata(table_name)
        
        if not table_metadata:
            return []
        
        # Use vector search to find relevant columns
        relevant_columns = self.metastore.search_schema(
            expected_output,
            filter={"table": table_name},
            top_k=10
        )
        
        # If specific columns are found, return them
        if relevant_columns:
            return relevant_columns
        
        # Otherwise, return all columns with reasonable defaults
        # Include key columns and common display columns like name, title, etc.
        key_columns = []
        display_columns = []
        
        for column in table_metadata.get("columns", []):
            column_name = column.get("name", "").lower()
            
            # Identify key columns (IDs)
            if column.get("is_primary_key", False) or "id" in column_name:
                key_columns.append(column)
            
            # Identify display columns
            if any(pattern in column_name for pattern in ["name", "title", "description", "status"]):
                display_columns.append(column)
        
        # Return key columns first, then display columns
        return key_columns + display_columns