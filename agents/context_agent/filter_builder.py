"""
Context Agent - Filter Builder

This module contains the FilterBuilder class which is responsible for 
constructing SQL filter conditions from extracted entities and temporal filters.
"""

import logging
import datetime
from typing import Dict, List, Any, Optional, Union

from text2sql.agents.context_agent.schema_mapper import SchemaMapper

logger = logging.getLogger(__name__)

class FilterBuilder:
    """
    The FilterBuilder constructs SQL filter conditions from extracted entities and temporal filters.
    """
    
    def __init__(self, schema_mapper: SchemaMapper):
        """
        Initialize the FilterBuilder with a SchemaMapper instance.
        
        Args:
            schema_mapper: An instance of SchemaMapper for resolving column references
        """
        self.schema_mapper = schema_mapper
    
    def build_filters(self, entities: List[Dict[str, Any]], 
                     temporal_filter: Optional[Dict[str, Any]],
                     table_name: str) -> List[Dict[str, Any]]:
        """
        Build filter specifications from entity extraction and temporal filtering.
        
        Args:
            entities: List of extracted entities from the Query Agent
            temporal_filter: Temporal filter information if present
            table_name: The primary table name
            
        Returns:
            A list of filter dictionaries
        """
        filters = []
        
        # Process entity-based filters
        for entity in entities:
            filter_spec = self._build_entity_filter(entity, table_name)
            if filter_spec:
                filters.append(filter_spec)
        
        # Process temporal filter if present
        if temporal_filter:
            date_filter = self._build_temporal_filter(temporal_filter, table_name)
            if date_filter:
                filters.append(date_filter)
        
        return filters
    
    def _build_entity_filter(self, entity: Dict[str, Any], 
                            table_name: str) -> Optional[Dict[str, Any]]:
        """
        Build a filter specification from an entity.
        
        Args:
            entity: The entity extracted from the query
            table_name: The primary table name
            
        Returns:
            A filter dictionary or None if the entity can't be mapped
        """
        entity_type = entity.get("entity_type", "")
        entity_value = entity.get("entity_value", "")
        mapped_column = entity.get("mapped_column", "")
        
        if not entity_type or not entity_value:
            return None
        
        try:
            # If no mapped column, try to find it using the schema mapper
            if not mapped_column:
                mapped_column, _ = self.schema_mapper.map_entity_to_column(
                    entity_type, entity_value, table_name
                )
            
            # Determine appropriate operator based on entity type and value
            operator = self._determine_operator(entity_type, entity_value)
            
            # Process the value based on operator and expected type
            processed_value = self._process_filter_value(entity_value, operator)
            
            return {
                "filter_name": entity_type,
                "column_name": mapped_column,
                "operator": operator,
                "value": processed_value
            }
            
        except ValueError as e:
            logger.warning(f"Could not build filter for entity {entity_type}:{entity_value}: {e}")
            return None
    
    def _build_temporal_filter(self, temporal_filter: Dict[str, Any], 
                              table_name: str) -> Optional[Dict[str, Any]]:
        """
        Build a filter specification from a temporal filter.
        
        Args:
            temporal_filter: The temporal filter information
            table_name: The primary table name
            
        Returns:
            A filter dictionary or None if no date column can be found
        """
        if not temporal_filter:
            return None
        
        # Find a date column in the table
        date_column = self.schema_mapper.find_date_column(table_name)
        
        if not date_column:
            logger.warning(f"No date column found in table {table_name} for temporal filtering")
            return None
        
        # Get the values from the temporal filter
        values = temporal_filter.get("value", [])
        conditional_statement = temporal_filter.get("conditional_statement", "")
        
        # If no explicit values are provided, try to resolve from the conditional statement
        if not values and conditional_statement:
            values = self._resolve_temporal_expression(conditional_statement)
        
        # Determine appropriate operator based on the values
        if isinstance(values, list) and len(values) == 2:
            operator = "BETWEEN"
        elif isinstance(values, str) or (isinstance(values, list) and len(values) == 1):
            operator = "="
            values = values[0] if isinstance(values, list) else values
        else:
            operator = ">"  # Default for unspecified temporal filters
        
        return {
            "filter_name": "date_range",
            "column_name": date_column,
            "operator": operator,
            "value": values
        }
    
    def _determine_operator(self, entity_type: str, entity_value: Any) -> str:
        """
        Determine the appropriate SQL operator based on entity type and value.
        
        Args:
            entity_type: The type of entity
            entity_value: The value of the entity
            
        Returns:
            The SQL operator to use
        """
        # Map of entity types to default operators
        operator_map = {
            "status": "=",
            "priority": "=",
            "category": "=",
            "type": "=",
            "count": ">",
            "amount": ">",
            "limit": "<=",
            "threshold": ">="
        }
        
        # Check for negation patterns in the value
        if isinstance(entity_value, str):
            if entity_value.lower().startswith(("not ", "isn't ", "is not ", "doesn't ", "does not ")):
                return "!="
            
            # Check for comparison indicators
            if entity_value.lower().startswith(("greater than", "more than", "over")):
                return ">"
            if entity_value.lower().startswith(("less than", "under", "below")):
                return "<"
            if entity_value.lower().startswith(("at least", "minimum")):
                return ">="
            if entity_value.lower().startswith(("at most", "maximum")):
                return "<="
        
        # Default to the entity type mapping or equality
        return operator_map.get(entity_type.lower(), "=")
    
    def _process_filter_value(self, value: Any, operator: str) -> Any:
        """
        Process a filter value based on the operator and expected type.
        
        Args:
            value: The raw filter value
            operator: The SQL operator
            
        Returns:
            The processed value
        """
        # Handle equality operators
        if operator in ["=", "!=", "<", ">", "<=", ">="]:
            # Clean string values
            if isinstance(value, str):
                # Extract numeric part if the value contains comparison words
                if any(word in value.lower() for word in ["than", "least", "most", "minimum", "maximum"]):
                    # Extract numeric value - simplified example
                    import re
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        return int(numbers[0])
                
                # Remove negation words
                for prefix in ["not ", "isn't ", "is not ", "doesn't ", "does not "]:
                    if value.lower().startswith(prefix):
                        return value[len(prefix):].strip()
                
                return value
            
            return value
        
        # Handle BETWEEN operator
        if operator == "BETWEEN":
            if isinstance(value, list) and len(value) == 2:
                return value
            elif isinstance(value, str) and " to " in value.lower():
                parts = value.split(" to ", 1)
                return [parts[0].strip(), parts[1].strip()]
            elif isinstance(value, str) and " - " in value:
                parts = value.split(" - ", 1)
                return [parts[0].strip(), parts[1].strip()]
            
            # If we can't extract a range, return the value as-is
            return value
        
        # Handle IN operator
        if operator == "IN":
            if isinstance(value, list):
                return value
            elif isinstance(value, str) and "," in value:
                return [item.strip() for item in value.split(",")]
            
            # Single value IN
            return [value]
        
        return value
    
    def _resolve_temporal_expression(self, expression: str) -> List[str]:
        """
        Resolve a temporal expression into concrete date values.
        
        Args:
            expression: A temporal expression like "last week", "yesterday", etc.
            
        Returns:
            A list of two date strings for a range, or a single date string
        """
        today = datetime.date.today()
        
        # Common temporal expressions
        if expression.lower() == "today":
            return [today.isoformat()]
        
        if expression.lower() == "yesterday":
            yesterday = today - datetime.timedelta(days=1)
            return [yesterday.isoformat()]
        
        if expression.lower() == "last week":
            end_date = today
            start_date = today - datetime.timedelta(days=7)
            return [start_date.isoformat(), end_date.isoformat()]
        
        if expression.lower() == "last month":
            end_date = today
            # Approximate a month as 30 days for simplicity
            start_date = today - datetime.timedelta(days=30)
            return [start_date.isoformat(), end_date.isoformat()]
        
        if expression.lower() == "this year":
            start_date = datetime.date(today.year, 1, 1)
            return [start_date.isoformat(), today.isoformat()]
        
        if expression.lower() == "last year":
            start_date = datetime.date(today.year - 1, 1, 1)
            end_date = datetime.date(today.year - 1, 12, 31)
            return [start_date.isoformat(), end_date.isoformat()]
        
        # Default to recent dates if expression can't be parsed
        end_date = today
        start_date = today - datetime.timedelta(days=30)  # Default to last 30 days
        
        logger.warning(f"Could not precisely resolve temporal expression: {expression}. Using last 30 days.")
        return [start_date.isoformat(), end_date.isoformat()]