"""
MetaStore for the Text2SQL system.

This module manages the metadata repository for database schemas, 
sample data, and vector embeddings used in the natural language to SQL conversion.
"""

import os
import json
import faiss
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from loguru import logger


class MetaStore:
    """
    Manages database metadata and provides semantic search capabilities
    for matching natural language queries to database schemas.
    """
    
    def __init__(self, vector_db_path: str, schema_dir: str, 
                 table_heads_dir: str, sql_pairs_dir: str,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the MetaStore.
        
        Args:
            vector_db_path: Path to the vector database directory
            schema_dir: Path to the database schema directory
            table_heads_dir: Path to the table sample data directory
            sql_pairs_dir: Path to the sample SQL pairs directory
            embedding_model: Name of the SentenceTransformer model to use
        """
        self.vector_db_path = vector_db_path
        self.schema_dir = schema_dir
        self.table_heads_dir = table_heads_dir
        self.sql_pairs_dir = sql_pairs_dir
        
        # Create directories if they don't exist
        for dir_path in [vector_db_path, schema_dir, table_heads_dir, sql_pairs_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Load embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize vector database components
        self.schema_index = None
        self.schema_texts = []
        self.schema_metadata = []
        
        # Load schema index if it exists
        self._load_or_create_indices()
    
    def _load_or_create_indices(self):
        """Load existing vector indices or create new ones."""
        schema_index_path = os.path.join(self.vector_db_path, "schema_index.faiss")
        metadata_path = os.path.join(self.vector_db_path, "schema_metadata.json")
        
        if os.path.exists(schema_index_path) and os.path.exists(metadata_path):
            try:
                # Load FAISS index
                self.schema_index = faiss.read_index(schema_index_path)
                
                # Load metadata
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                    self.schema_texts = data.get('texts', [])
                    self.schema_metadata = data.get('metadata', [])
                
                logger.info(f"Loaded existing schema index with {len(self.schema_texts)} entries")
                return
            except Exception as e:
                logger.error(f"Error loading indices: {str(e)}")
        
        # Create new indices if loading failed or files don't exist
        self.schema_index = faiss.IndexFlatL2(self.embedding_dimension)
        self.schema_texts = []
        self.schema_metadata = []
        logger.info("Created new schema indices")
    
    def _save_indices(self):
        """Save vector indices and metadata to disk."""
        schema_index_path = os.path.join(self.vector_db_path, "schema_index.faiss")
        metadata_path = os.path.join(self.vector_db_path, "schema_metadata.json")
        
        try:
            # Save FAISS index
            faiss.write_index(self.schema_index, schema_index_path)
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump({
                    'texts': self.schema_texts,
                    'metadata': self.schema_metadata
                }, f, indent=2)
            
            logger.info(f"Saved schema index with {len(self.schema_texts)} entries")
            return True
        except Exception as e:
            logger.error(f"Error saving indices: {str(e)}")
            return False
    
    def index_schema_data(self):
        """
        Index database schema information from the schema directory.
        This creates vector embeddings for tables and columns for semantic search.
        """
        try:
            # Clear existing index
            self.schema_index = faiss.IndexFlatL2(self.embedding_dimension)
            self.schema_texts = []
            self.schema_metadata = []
            
            # Get all schema files
            schema_files = [f for f in os.listdir(self.schema_dir) 
                           if f.endswith('_schema.json') and not f.startswith('complete')]
            
            for schema_file in schema_files:
                with open(os.path.join(self.schema_dir, schema_file), 'r') as f:
                    schema_data = json.load(f)
                
                table_name = schema_data.get('table_name', '')
                if not table_name:
                    continue
                
                # Index table name with description
                table_text = f"Table: {table_name}"
                # Add table-level entry to index
                self._add_to_index(
                    text=table_text,
                    metadata={
                        'type': 'table',
                        'table_name': table_name,
                        'file': schema_file
                    }
                )
                
                # Index each column with its type
                for column in schema_data.get('columns', []):
                    column_name = column.get('name', '')
                    column_type = column.get('type', '')
                    
                    if not column_name:
                        continue
                    
                    # Add a column-level entry
                    column_text = f"Column: {column_name} in table {table_name} with type {column_type}"
                    self._add_to_index(
                        text=column_text,
                        metadata={
                            'type': 'column',
                            'table_name': table_name,
                            'column_name': column_name,
                            'column_type': column_type,
                            'file': schema_file
                        }
                    )
                
                # Index foreign key relationships
                for fk in schema_data.get('foreign_keys', []):
                    constrained_cols = fk.get('constrained_columns', [])
                    referred_table = fk.get('referred_table', '')
                    referred_cols = fk.get('referred_columns', [])
                    
                    if not constrained_cols or not referred_table or not referred_cols:
                        continue
                    
                    # Create a description of the foreign key relationship
                    fk_text = f"Foreign Key: {', '.join(constrained_cols)} in table {table_name} references {', '.join(referred_cols)} in table {referred_table}"
                    self._add_to_index(
                        text=fk_text,
                        metadata={
                            'type': 'foreign_key',
                            'table_name': table_name,
                            'constrained_columns': constrained_cols,
                            'referred_table': referred_table,
                            'referred_columns': referred_cols,
                            'file': schema_file
                        }
                    )
            
            # Save the updated indices
            self._save_indices()
            logger.info(f"Successfully indexed schema data from {len(schema_files)} tables")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing schema data: {str(e)}")
            return False
    
    def _add_to_index(self, text: str, metadata: Dict[str, Any]):
        """
        Add a text entry with metadata to the vector index.
        
        Args:
            text: Text to embed and index
            metadata: Associated metadata to store
        """
        # Get embedding and add to FAISS index
        embedding = self.embedding_model.encode([text])[0]
        self.schema_index.add(np.array([embedding], dtype=np.float32))
        
        # Store text and metadata
        self.schema_texts.append(text)
        self.schema_metadata.append(metadata)
    
    def search_schema(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the schema index for relevant database elements.
        
        Args:
            query: Natural language query to search for
            k: Number of results to return
            
        Returns:
            List of dictionaries containing matched schema elements with their metadata
        """
        if not self.schema_index or self.schema_index.ntotal == 0:
            logger.warning("Schema index is empty, nothing to search")
            return []
        
        # Compute query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search the index
        k = min(k, self.schema_index.ntotal)
        distances, indices = self.schema_index.search(query_embedding, k)
        
        # Collect results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.schema_texts) and idx >= 0:
                results.append({
                    'text': self.schema_texts[idx],
                    'metadata': self.schema_metadata[idx],
                    'distance': float(distances[0][i])
                })
        
        return results
    
    def get_schema_for_table(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a specific table.
        
        Args:
            table_name: Name of the table to get schema for
            
        Returns:
            Dictionary containing table schema or empty dict if not found
        """
        schema_file = os.path.join(self.schema_dir, f"{table_name}_schema.json")
        if not os.path.exists(schema_file):
            logger.warning(f"Schema file for table {table_name} not found")
            return {}
        
        try:
            with open(schema_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schema for table {table_name}: {str(e)}")
            return {}
    
    def get_sample_data_for_table(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get sample data for a specific table.
        
        Args:
            table_name: Name of the table to get samples for
            
        Returns:
            Dictionary containing sample data or None if not found
        """
        sample_file = os.path.join(self.table_heads_dir, f"{table_name}_samples.json")
        if not os.path.exists(sample_file):
            logger.warning(f"Sample data for table {table_name} not found")
            return None
        
        try:
            with open(sample_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sample data for table {table_name}: {str(e)}")
            return None


if __name__ == "__main__":
    # Example usage
    metastore = MetaStore(
        vector_db_path="metastore/vector_db",
        schema_dir="metastore/db_metadata",
        table_heads_dir="metastore/table_heads",
        sql_pairs_dir="metastore/sql_pairs"
    )
    
    # Index schema data
    metastore.index_schema_data()
    
    # Example search
    results = metastore.search_schema("Find all user orders")
    for result in results:
        print(f"Match: {result['text']}")
        print(f"Metadata: {result['metadata']}")
        print(f"Distance: {result['distance']}")
        print("---")