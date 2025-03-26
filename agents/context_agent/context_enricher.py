"""
Context Agent - Context Enricher

This module contains the ContextEnricher class which is responsible for transforming 
decomposed queries from the Query Agent into contextual data by leveraging the MetaStore.
"""

import json
import logging
from typing import Dict, List, Any, Optional

# Assuming this will be created in the project
from text2sql.metastore.metastore import MetaStore

logger = logging.getLogger(__name__)

class ContextEnricher:
    """
    The ContextEnricher is responsible for enriching decomposed queries with
    schema metadata from the MetaStore to produce contextual data for SQL generation.
    """
    
    def __init__(self, metastore: MetaStore):
        """
        Initialize the ContextEnricher with a MetaStore instance.
        
        Args:
            metastore: An instance of MetaStore for retrieving database metadata
        """
        self.metastore = metastore
    
    def enrich_query(self, decomposed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a decomposed query into enriched contextual data.
        
        Args:
            decomposed_query: The structured output from the Query Agent
            
        Returns:
            A dictionary containing the enriched contextual data for SQL generation
        """
        logger.info("Enriching decomposed query with context")
        
        # Initialize the contextual data structure
        contextual_data = self._initialize_contextual_data(decomposed_query)
        
        # Determine the primary table based on intent and entities
        primary_table = self._determine_primary_table(decomposed_query)
        
        # Add table metadata to contextual data
        contextual_data["table_metadata"] = self._get_table_metadata(primary_table)
        
        # Build filters from entity extraction and temporal filtering
        contextual_data["filters"] = self._build_filters(decomposed_query, primary_table)
        
        # Determine output columns based on the expected output and intent
        contextual_data["output_columns"] = self._determine_output_columns(
            decomposed_query, primary_table
        )
        
        # Validate the completeness of the contextual data
        self._validate_contextual_data(contextual_data)
        
        return contextual_data
    
    def _initialize_contextual_data(self, decomposed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize the basic structure of the contextual data from the decomposed query.
        
        Args:
            decomposed_query: The structured output from the Query Agent
            
        Returns:
            A dictionary with the basic contextual data structure
        """
        decomp = decomposed_query.get("query_decomposition", {})
        
        return {
            "intent": decomp.get("intent", {}).get("goal", ""),
            "context": {
                "description": decomp.get("context", {}).get("description", ""),
                "expected_output": decomp.get("context", {}).get("expected_output", "")
            }
        }
    
    def _determine_primary_table(self, decomposed_query: Dict[str, Any]) -> str:
        """
        Determine the primary table for the query using intent and entities.
        
        Args:
            decomposed_query: The structured output from the Query Agent
            
        Returns:
            The name of the primary table
        """
        decomp = decomposed_query.get("query_decomposition", {})
        intent = decomp.get("intent", {}).get("goal", "")
        
        # Extract entities for vector search
        entities = []
        for entity in decomp.get("entity_extraction", []):
            entities.append(entity.get("entity_type", ""))
            entities.append(entity.get("entity_value", ""))
        
        # Combine intent and entities for semantic search
        search_query = f"{intent} {' '.join(entities)}"
        
        # Search for relevant tables in the MetaStore
        relevant_tables = self.metastore.search_schema(search_query, top_k=3)
        
        if not relevant_tables:
            raise ValueError("No relevant tables found for the query")
        
        # Return the most relevant table
        return relevant_tables[0]["name"]
    
    def _get_table_metadata(self, table_name: str) -> Dict[str, Any]:
        """
        Retrieve metadata for the primary table.
        
        Args:
            table_name: The name of the primary table
            
        Returns:
            A dictionary containing table metadata
        """
        table_metadata = self.metastore.get_table_metadata(table_name)
        
        if not table_metadata:
            raise ValueError(f"No metadata found for table {table_name}")
        
        # Format the table fields
        table_fields = {}
        for column in table_metadata.get("columns", []):
            table_fields[column["name"]] = column["data_type"]
        
        return {
            "primary_table": table_name,
            "table_description": table_metadata.get("description", ""),
            "table_fields": table_fields
        }
    
    def _build_filters(self, decomposed_query: Dict[str, Any], table_name: str) -> List[Dict[str, Any]]:
        """
        Build filters from entity extraction and temporal filtering.
        
        Args:
            decomposed_query: The structured output from the Query Agent
            table_name: The name of the primary table
            
        Returns:
            A list of filter dictionaries
        """
        filters = []
        decomp = decomposed_query.get("query_decomposition", {})
        
        # Process entity extraction for filters
        for entity in decomp.get("entity_extraction", []):
            entity_type = entity.get("entity_type", "")
            entity_value = entity.get("entity_value", "")
            mapped_column = entity.get("mapped_column", "")
            
            # If no mapped column, try to find it using the MetaStore
            if not mapped_column:
                mapped_column = self._map_entity_to_column(entity_type, entity_value, table_name)
            
            # Determine appropriate operator
            operator = self._determine_operator(entity_type, entity_value)
            
            filters.append({
                "filter_name": entity_type,
                "column_name": mapped_column,
                "operator": operator,
                "value": entity_value
            })
        
        # Process temporal filtering if present
        temporal = decomp.get("temporal_filtering", {})
        if temporal:
            date_column = self._find_date_column(table_name)
            
            if date_column:
                filters.append({
                    "filter_name": "date_range",
                    "column_name": date_column,
                    "operator": "BETWEEN",
                    "value": temporal.get("value", [])
                })
        
        return filters
    
    def _map_entity_to_column(self, entity_type: str, entity_value: str, table_name: str) -> str:
        """
        Map an entity to a database column using the MetaStore.
        
        Args:
            entity_type: The type of entity extracted
            entity_value: The value of the extracted entity
            table_name: The name of the table
            
        Returns:
            The name of the mapped column
        """
        # Search in column metadata
        query = f"{entity_type} {entity_value}"
        columns = self.metastore.search_schema(query, filter={"table": table_name}, top_k=3)
        
        if not columns:
            # If no columns found by semantic search, try table heads
            sample_matches = self.metastore.search_table_heads(entity_value, table_name=table_name)
            if sample_matches and sample_matches[0].get("column_name"):
                return sample_matches[0]["column_name"]
            raise ValueError(f"Could not map entity {entity_type}:{entity_value} to a column")
        
        # Return the highest scoring column match
        return columns[0]["name"]
    
    def _determine_operator(self, entity_type: str, entity_value: Any) -> str:
        """
        Determine the appropriate SQL operator based on entity type and value.
        
        Args:
            entity_type: The type of entity extracted
            entity_value: The value of the extracted entity
            
        Returns:
            The SQL operator to use
        """
        # Simple mapping of entity types to operators
        # This would be expanded based on the system's entity type taxonomy
        operator_map = {
            "status": "=",
            "priority": "=",
            "category": "=",
            "type": "=",
            "count": ">",
            "amount": ">",
            "limit": "<="
        }
        
        # Default to equality for most entity types
        return operator_map.get(entity_type, "=")
    
    def _find_date_column(self, table_name: str) -> Optional[str]:
        """
        Find a date column in the table for temporal filtering.
        
        Args:
            table_name: The name of the table
            
        Returns:
            The name of the date column, or None if not found
        """
        table_metadata = self.metastore.get_table_metadata(table_name)
        
        if not table_metadata:
            return None
        
        # Look for date/time columns
        date_columns = []
        for column in table_metadata.get("columns", []):
            data_type = column.get("data_type", "").upper()
            column_name = column.get("name", "")
            
            # Check data type or name patterns for date columns
            if any(dt in data_type for dt in ["DATE", "TIME", "TIMESTAMP"]):
                date_columns.append(column_name)
            elif any(pattern in column_name.lower() for pattern in ["date", "time", "created", "updated", "timestamp"]):
                date_columns.append(column_name)
        
        return date_columns[0] if date_columns else None
    
    def _determine_output_columns(self, decomposed_query: Dict[str, Any], table_name: str) -> List[Dict[str, Any]]:
        """
        Determine which columns should be included in the output based on intent and expected output.
        
        Args:
            decomposed_query: The structured output from the Query Agent
            table_name: The name of the primary table
            
        Returns:
            A list of output column dictionaries
        """
        decomp = decomposed_query.get("query_decomposition", {})
        intent = decomp.get("intent", {}).get("goal", "")
        expected_output = decomp.get("context", {}).get("expected_output", "")
        
        # Get the table metadata
        table_metadata = self.metastore.get_table_metadata(table_name)
        if not table_metadata:
            raise ValueError(f"No metadata found for table {table_name}")
        
        # If the intent is to count or aggregate, limit the columns
        if intent.startswith("count_") or intent.startswith("aggregate_"):
            # For count or aggregate queries, usually only need key columns
            return self._get_key_columns(table_metadata)
        
        # For retrieval queries, find relevant columns based on expected output
        relevant_columns = self.metastore.get_relevant_columns(table_name, expected_output)
        
        # If no relevant columns found, include all columns
        if not relevant_columns:
            relevant_columns = table_metadata.get("columns", [])
        
        # Format the output columns
        output_columns = []
        for column in relevant_columns:
            output_column = {
                "column_name": column["name"],
                "alias": column.get("display_name", self._format_column_name(column["name"])),
                "column_description": column.get("description", ""),
                "column_fields": {
                    "data_type": column["data_type"],
                    "nullable": column.get("nullable", True)
                }
            }
            output_columns.append(output_column)
        
        return output_columns
    
    def _get_key_columns(self, table_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get primary key and important columns for aggregate queries.
        
        Args:
            table_metadata: Metadata for the table
            
        Returns:
            A list of key column dictionaries formatted for output
        """
        key_columns = []
        
        # Find primary key or important columns
        for column in table_metadata.get("columns", []):
            if column.get("is_primary_key", False) or "id" in column["name"].lower():
                key_column = {
                    "column_name": column["name"],
                    "alias": self._format_column_name(column["name"]),
                    "column_description": column.get("description", ""),
                    "column_fields": {
                        "data_type": column["data_type"],
                        "nullable": column.get("nullable", True)
                    }
                }
                key_columns.append(key_column)
        
        return key_columns
    
    def _format_column_name(self, column_name: str) -> str:
        """
        Format a column name for display.
        
        Args:
            column_name: The raw column name from the database
            
        Returns:
            A formatted display name
        """
        return column_name.replace("_", " ").title()
    
    def _validate_contextual_data(self, contextual_data: Dict[str, Any]) -> None:
        """
        Validate the completeness of the contextual data.
        
        Args:
            contextual_data: The completed contextual data
            
        Raises:
            ValueError: If the contextual data is incomplete
        """
        required_fields = ["intent", "context", "filters", "table_metadata", "output_columns"]
        
        for field in required_fields:
            if field not in contextual_data or not contextual_data[field]:
                raise ValueError(f"Contextual data missing required field: {field}")
        
        # Validate table metadata
        table_meta = contextual_data.get("table_metadata", {})
        if not table_meta.get("primary_table"):
            raise ValueError("Table metadata missing primary table")
        
        # Validate output columns
        if not contextual_data.get("output_columns"):
            raise ValueError("No output columns specified")