# Text2SQL: Multi-Agent SQL Query Generation

A sophisticated natural language to SQL query conversion system using a multi-agent architecture.

## Overview

Text2SQL converts natural language queries into precise SQL statements using a three-agent pipeline:

1. **Query Agent**: Decomposes natural language into structured components
2. **Context Agent**: Enriches queries with database metadata through vector search
3. **Schema Agent**: Generates and validates SQL with iterative correction

## Architecture

The system uses a modular architecture as detailed in [architecture.md](architecture.md):

- **Meta Store**: Central repository for database metadata, sample data, and SQL examples
- **Vector Embeddings**: For semantic matching of queries to database elements
- **Iterative Validation**: Multiple checkpoints to ensure accurate SQL generation

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/text2sql.git
cd text2sql

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
text2sql/
├── agents/                      # Contains the three main agent components
│   ├── query_agent/             # Handles query decomposition
│   ├── context_agent/           # Manages context enrichment
│   └── schema_agent/            # Performs SQL generation and validation
├── metastore/                   # Stores and manages all metadata
├── templates/                   # SQL templates for query generation
├── utils/                       # Shared utilities and helper functions
├── config/                      # Configuration files
├── tests/                       # Unit and integration tests
├── examples/                    # Example queries and results
└── docs/                        # Documentation files
```

For a detailed description of each component, see [docs/project_structure.md](docs/project_structure.md).

## Usage

Coming soon.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This architecture is based on advancements in LLMs and RAG systems
- Inspired by challenges in making database querying accessible to non-technical users