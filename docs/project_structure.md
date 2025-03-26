# Text2SQL Project Structure

This document outlines the organization and structure of the Text2SQL system, which converts natural language queries into SQL. The system uses a multi-agent architecture as detailed in `architecture.md`.

## Directory Structure

```
text2sql/
├── architecture.md              # High-level architectural overview document
├── agents/                      # Contains the three main agent components
│   ├── query_agent/             # Handles query decomposition
│   ├── context_agent/           # Manages context enrichment
│   └── schema_agent/            # Performs SQL generation and validation
├── metastore/                   # Stores and manages all metadata for the system
│   ├── db_metadata/             # Database schema information
│   ├── table_heads/             # Sample data from tables
│   ├── sql_pairs/               # Natural language to SQL mapping examples
│   ├── embeddings/              # Vector embeddings for metadata
│   ├── vector_db/               # Vector database files
│   ├── extract_schema.py        # Utility for extracting database schema
│   ├── sample_tables.py         # Utility for collecting sample data
│   ├── create_embeddings.py     # Utility for generating embeddings
│   ├── setup_vector_db.py       # Utility for setting up vector database
│   └── metastore.py             # Main access layer for the metastore
├── templates/                   # SQL templates for query generation
├── utils/                       # Shared utilities and helper functions
├── config/                      # Configuration files
├── tests/                       # Unit and integration tests
├── examples/                    # Example queries and results
└── docs/                        # Documentation files
```

## Component Descriptions

### Agents

#### Query Agent (`agents/query_agent/`)
- **Purpose**: Decomposes natural language queries into structured components
- **Responsibilities**:
  - Extract user intent
  - Identify context and expected output
  - Detect temporal filters
  - Extract entities (tables, columns, conditions)
- **Key Files**: 
  - `query_processor.py`: Main processing logic
  - `entity_extraction.py`: NER and entity identification
  - `temporal_parser.py`: Parse time-related expressions

#### Context Agent (`agents/context_agent/`)
- **Purpose**: Enriches decomposed queries with schema metadata
- **Responsibilities**:
  - Retrieve relevant schema metadata via vector search
  - Map NL entities to database columns
  - Build contextual data with filters and output columns
- **Key Files**:
  - `context_enricher.py`: Main enrichment logic
  - `schema_mapper.py`: Maps entities to schema components
  - `filter_builder.py`: Constructs SQL filter conditions

#### Schema Agent (`agents/schema_agent/`)
- **Purpose**: Generates and validates SQL queries
- **Responsibilities**:
  - Construct SQL using templates
  - Validate syntax and semantics
  - Handle errors through iterative refinement
- **Key Files**:
  - `sql_generator.py`: Main SQL generation logic
  - `sql_validator.py`: SQL validation and error handling
  - `template_manager.py`: Manages SQL templates

### Metastore (`metastore/`)

- **Purpose**: Central repository for all metadata and embeddings
- **Components**:
  - **DB Metadata** (`db_metadata/`): Schema information (tables, columns, relationships)
  - **Table Heads** (`table_heads/`): Sample data from tables
  - **SQL Pairs** (`sql_pairs/`): Examples of NL-to-SQL mappings
  - **Embeddings** (`embeddings/`): Vector representations of metadata
  - **Vector DB** (`vector_db/`): Vector database for similarity search

- **Utilities**:
  - `extract_schema.py`: Extracts schema from databases
  - `sample_tables.py`: Collects sample data from tables
  - `create_embeddings.py`: Generates vector embeddings
  - `setup_vector_db.py`: Sets up vector database
  - `metastore.py`: Main access layer for the metastore

### Templates (`templates/`)
- SQL templates for different query types (SELECT, INSERT, etc.)
- May include Jinja2 templates for dynamic SQL generation

### Utils (`utils/`)
- Shared utility functions
- Database connectors
- Logging and error handling

### Config (`config/`)
- Configuration files for:
  - Database connections
  - Embedding models
  - Agent parameters
  - Vector database settings

### Tests (`tests/`)
- Unit tests for individual components
- Integration tests for the full pipeline
- Test fixtures and mock data

### Examples (`examples/`)
- Sample NL queries and expected SQL output
- Demo scripts and notebooks

### Docs (`docs/`)
- Detailed documentation for each component
- API references
- Usage examples
- Implementation guides

## File Formats

### Agent Communication Formats

The agents communicate using structured JSON formats:

1. **Query Agent Output**:
```json
{
  "query": "Show me all open tickets from last week",
  "query_decomposition": {
    "context": {
      "description": "Fetch ticket records filtered by status and date range.",
      "expected_output": "List of ticket IDs, statuses, and creation dates"
    },
    "intent": {
      "goal": "retrieve_tickets"
    },
    "temporal_filtering": {
      "conditional_statement": "last week",
      "value": ["2025-03-17", "2025-03-24"]
    },
    "entity_extraction": [
      {
        "entity_type": "ticket_status",
        "entity_value": "open",
        "mapped_column": "ticket_status"
      }
    ]
  }
}
```

2. **Context Agent Output**:
```json
{
  "intent": "retrieve_tickets",
  "context": {
    "description": "Retrieve all open tickets from last week",
    "expected_output": "List of ticket details including ID, status, and creation date"
  },
  "filters": [
    {
      "filter_name": "status",
      "column_name": "ticket_status",
      "operator": "=",
      "value": "open"
    },
    {
      "filter_name": "date_range",
      "column_name": "created_date",
      "operator": "BETWEEN",
      "value": ["2025-03-17", "2025-03-24"]
    }
  ],
  "table_metadata": {
    "primary_table": "tickets",
    "table_description": "Contains all support ticket records",
    "table_fields": {
      "ticket_id": "INT",
      "ticket_status": "VARCHAR",
      "created_date": "DATETIME",
      "assigned_to": "VARCHAR"
    }
  },
  "output_columns": [
    {
      "column_name": "ticket_id",
      "alias": "Ticket ID",
      "column_description": "Unique identifier for each ticket",
      "column_fields": {
        "data_type": "INT",
        "nullable": false
      }
    },
    /* Additional columns */
  ]
}
```

3. **Schema Agent Output**: The final SQL query string.

---

*This document will be updated as the system evolves with additional details on implementation, data flows, and component interactions.*