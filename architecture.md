Below is an in‑depth architectural paper that covers the entire Text‑to‑SQL pipeline—from the problem statement to the proposed multi‑agent solution, detailed component descriptions, input/output formats, and the mechanisms for processing natural language into executable SQL queries.

---

# Text-to-SQL: A Multi-Agent Architecture for Dynamic SQL Query Generation

## Abstract

The exponential growth of structured and unstructured data has led to an increased need for accessible data analytics. Non‑technical users often struggle to retrieve insights from relational databases due to the complexity of SQL. This paper presents a comprehensive architecture that converts natural language (NL) queries into precise SQL statements using a three‑agent pipeline: a Query Agent for query decomposition, a Context Agent for semantic enrichment via metadata retrieval, and a Schema Manager for SQL synthesis and validation. We discuss the problem space, detailed component design—including inputs, outputs, and underlying mechanisms—and strategies for validation and error handling. This architecture leverages vector embeddings for database metadata and table heads, dynamic retrieval, iterative error correction, and inter‑agent communication through structured JSON.

## 1. Introduction

As enterprises increasingly rely on relational databases, the ability to extract insights via SQL queries becomes critical. However, writing SQL requires specialized expertise. Text‑to‑SQL systems have emerged as a solution, enabling users to query data in natural language and have the system generate corresponding SQL. With advancements in large language models (LLMs) and Retrieval Augmented Generation (RAG), it is now possible to build robust systems that bridge this gap.

Despite these advancements, significant challenges remain:
- **Natural Language Ambiguity:** NL queries are inherently ambiguous, making it difficult to map them directly to precise SQL.
- **Schema Complexity:** Enterprise databases often have complex schemas with numerous tables, columns, and relationships.
- **Error Recovery:** Generated SQL must be validated and refined to avoid syntax errors and semantic mismatches.
- **Scalability:** Systems must handle growing datasets and evolving schemas.

This paper outlines a multi‑agent architecture designed to overcome these challenges.

## 2. Problem Statement

The primary problem addressed is the conversion of NL queries into syntactically and semantically correct SQL queries that can be executed on complex database schemas. Key challenges include:

- **Query Decomposition:** Extracting intent, context, temporal filters, and entities from the NL query.
- **Schema Linking:** Mapping extracted entities to actual database columns and tables using metadata.
- **SQL Generation:** Crafting SQL statements that reflect both the user’s intent and the underlying schema.
- **Validation and Correction:** Incorporating error handling mechanisms to iteratively refine SQL queries based on feedback.

## 3. Proposed Architecture

The solution is built as a pipeline of three main agents:

1. **Query Agent:** Decomposes the user’s natural language query into structured parameters.
2. **Context Agent:** Enriches the decomposed query by retrieving and aligning relevant metadata (e.g., DB schema, table heads, SQL pairs) using vector-based retrieval.
3. **Schema Manager:** Synthesizes and validates the SQL query based on the enriched context, utilizing iterative error correction and validation loops.

A unified Meta Store supports the Context and Schema agents by providing:
- **DB Metadata:** Schema information (table names, columns, data types) embedded as vectors for semantic matching.
- **Table Heads:** Sample data from tables, also vectorized, to aid in resolving ambiguous entity mappings.
- **SQL Pairs:** A dictionary of natural language query–SQL pairs for refining SQL generation.

### 3.1 High-Level Workflow

1. **User Query Submission:**  
   - **Input:** A natural language query, e.g., “Show me all open tickets from last week.”
2. **Query Decomposition (Query Agent):**  
   - **Input:** NL query.  
   - **Output:** Structured JSON containing:  
     - *Intent:* The high-level goal (e.g., `retrieve_tickets`).  
     - *Context:* A refined description and expected output (e.g., “Fetch ticket details with status ‘open’.”).  
     - *Temporal Filtering & Entity Extraction:* Filters like date range and entities such as ticket status.  
3. **Context Enrichment (Context Agent):**  
   - **Input:** Decomposed JSON from the Query Agent.  
   - **Mechanism:**  
     - Retrieve relevant metadata from the Meta Store via vector search.  
     - Map NL entities to specific database columns using semantic similarity measures.  
   - **Output:** A “Contextual Data” JSON that includes enriched details:  
     - *Table Metadata:* Primary table and schema details.  
     - *Filters:* Mapped filter conditions with SQL operators.  
     - *Output Columns:* Columns to be included in the SELECT clause.
4. **SQL Query Generation (Schema Manager):**  
   - **Input:** Contextual Data JSON and the original NL query.  
   - **Mechanism:**  
     - Construct a SQL skeleton using a template-based approach (e.g., via Jinja2).  
     - Integrate filters into the WHERE clause, ensuring proper joins and column qualification.  
     - Validate the SQL using parsing libraries or dry-run checks (e.g., EXPLAIN).  
     - Use iterative error feedback loops to refine the query if errors are detected.
   - **Output:** A syntactically and semantically correct SQL query.
5. **SQL Execution and Result Retrieval:**  
   - **Input:** The final SQL query.  
   - **Mechanism:** Execute the query on the actual database and retrieve results.  
   - **Output:** SQL data that is optionally formatted into natural language by a Decorator module.

## 4. Core Components and Their Mechanisms

### 4.1 Query Agent

- **Function:** Decompose the NL query into structured components.
- **Input Format:** Plain text query.
- **Output Format:** JSON, e.g.,

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

- **Mechanisms:**  
  - NLP parsing using LLMs or rule‑based systems (e.g., spaCy, GPT‑4 prompts).  
  - Named Entity Recognition (NER) to extract entities and conditions.

### 4.2 Context Agent

- **Function:** Enrich the decomposed query with schema metadata.
- **Input:** Decomposed JSON from the Query Agent.
- **Output Format:** Contextual Data JSON, e.g.,

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
      {
        "column_name": "ticket_status",
        "alias": "Status",
        "column_description": "Status of the ticket (open/closed)",
        "column_fields": {
          "data_type": "VARCHAR",
          "nullable": false
        }
      },
      {
        "column_name": "created_date",
        "alias": "Creation Date",
        "column_description": "Date and time when the ticket was created",
        "column_fields": {
          "data_type": "DATETIME",
          "nullable": false
        }
      }
    ]
  }
  ```

- **Mechanisms:**  
  - Retrieve schema metadata from the Meta Store via vector search (using FAISS, HNSW, etc.).  
  - Map extracted NL entities to database schema using semantic similarity measures.  
  - Use JSON Schema validation to ensure consistency.

### 4.3 Schema Manager

- **Function:** Generate and validate the final SQL query.
- **Input:** Contextual Data JSON (from the Context Agent) and the original NL query.
- **Output:** A final SQL query string, e.g.,

  ```sql
  SELECT ticket_id AS "Ticket ID", ticket_status AS "Status", created_date AS "Creation Date"
  FROM tickets
  WHERE ticket_status = 'open'
    AND created_date BETWEEN '2025-03-17' AND '2025-03-24';
  ```

- **Mechanisms:**  
  - Template-based SQL generation using templating tools (e.g., Jinja2).  
  - Dynamic construction of the SELECT clause from `output_columns`.  
  - Generation of the WHERE clause by integrating filters.  
  - Validation using SQL parsers (e.g., sqlparse) or dry-run/explain commands to check for syntax and schema correctness.  
  - Iterative error handling: If validation fails, capture error messages and re-prompt the LLM (or agent) with corrective instructions until a valid query is produced.

## 5. Validation and Error Handling Mechanisms

Validation is embedded at multiple stages:
- **Post Query Decomposition:** JSON Schema and rule‑based checks verify that all required components are present.
- **During Context Enrichment:** Similarity scores from vector searches confirm that retrieved metadata is reliable and corresponds to the extracted entities.
- **During SQL Generation:**  
  - A SQL parsing library or EXPLAIN command is used to validate the SQL syntax.  
  - An iterative feedback loop re‑prompts the LLM if errors (e.g., missing columns, ambiguous joins) are detected.
- **Post SQL Execution:** Query results are compared against expected patterns (using heuristics or domain‑specific rules), triggering further corrections if discrepancies are found.

## 6. Discussion

The proposed multi‑agent architecture leverages the strengths of LLMs combined with structured metadata retrieval and iterative query refinement to generate accurate SQL queries from NL inputs. By segmenting the process into Query, Context, and Schema stages, the system isolates complexity and enables targeted error handling. This modular approach ensures that each agent specializes in its task, reducing the likelihood of cascading errors.

The use of vector embeddings for DB metadata and table heads enhances semantic matching, ensuring that the context is dynamically enriched based on the user’s query. Moreover, by passing structured JSON between agents, the architecture maintains clarity and consistency in data exchange. Iterative error handling further guarantees that the final SQL query is both syntactically correct and semantically aligned with the user’s intent.

## 7. Conclusion

Our multi-agent Text‑to‑SQL architecture provides a robust framework for transforming natural language queries into accurate, executable SQL statements. The system’s design—comprising a Query Agent, Context Agent, and Schema Manager—enables:
- Effective decomposition of NL queries,
- Dynamic enrichment with contextual metadata,
- Precise SQL query generation and iterative validation.

By leveraging vector-based retrieval and structured JSON communication between agents, the architecture addresses key challenges such as schema ambiguity, natural language variability, and error correction, making it a scalable solution for enterprise data querying.

This paper outlines both the theoretical foundations and practical mechanisms behind our approach, offering a blueprint for building advanced Text‑to‑SQL systems that democratize data access for non‑technical users.

---

Would you like additional details on specific components or a deeper dive into any section?