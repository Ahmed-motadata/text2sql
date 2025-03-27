// Text to SQL conversion service
const path = require('path');

/**
 * Service for converting natural language queries to SQL
 */
class Text2SQLService {
  /**
   * Convert natural language query to SQL using structured decomposition
   * @param {string} nlQuery - Natural language query
   * @param {Object} dbSchema - Database schema information
   * @returns {Promise<Object>} Generated SQL query and explanation
   */
  async generateSQL(nlQuery, dbSchema) {
    try {
      // Parse the query into structured components
      const queryComponents = this._decomposeQuery(nlQuery);
      const tables = Object.keys(dbSchema);
      
      // Find relevant table based on intent and entities
      const targetTable = this._findRelevantTable(queryComponents, tables, dbSchema);
      if (!targetTable) {
        throw new Error('Could not determine target table');
      }

      // Get columns for the table
      const tableColumns = dbSchema[targetTable].columns.map(col => col.column_name);
      
      // Build SQL query using the decomposed components
      const sql = this._buildSQLQuery(targetTable, tableColumns, queryComponents, dbSchema);
      
      return {
        sql,
        explanation: `Generated a query to ${queryComponents.intent.goal} from the ${targetTable} table.`
      };
    } catch (error) {
      console.error('Error generating SQL:', error);
      throw error;
    }
  }

  /**
   * Decompose the query into structured components
   * @private
   */
  _decomposeQuery(nlQuery) {
    // Basic query decomposition structure
    return {
      context: {
        description: nlQuery,
        expected_output: this._determineExpectedOutput(nlQuery)
      },
      intent: {
        goal: this._determineQueryGoal(nlQuery)
      },
      temporal_filtering: this._extractTemporalFiltering(nlQuery),
      entity_extraction: this._extractEntities(nlQuery)
    };
  }

  /**
   * Determine the expected output format
   * @private
   */
  _determineExpectedOutput(nlQuery) {
    if (nlQuery.includes('how many') || nlQuery.includes('count')) {
      return 'count';
    }
    if (nlQuery.includes('average') || nlQuery.includes('avg')) {
      return 'aggregate';
    }
    return 'list';
  }

  /**
   * Determine the query goal
   * @private
   */
  _determineQueryGoal(nlQuery) {
    if (nlQuery.includes('show') || nlQuery.includes('get') || nlQuery.includes('list')) {
      return 'retrieve_records';
    }
    if (nlQuery.includes('count') || nlQuery.includes('how many')) {
      return 'count_records';
    }
    if (nlQuery.includes('average') || nlQuery.includes('avg')) {
      return 'aggregate_records';
    }
    return 'retrieve_records';
  }

  /**
   * Extract temporal filtering conditions
   * @private
   */
  _extractTemporalFiltering(nlQuery) {
    const temporal = {
      conditional_statement: null,
      value: [null, null]
    };

    if (nlQuery.includes('last')) {
      temporal.conditional_statement = 'last_n_days';
      if (nlQuery.includes('week')) {
        temporal.value = ['NOW() - INTERVAL \'7 days\'', 'NOW()'];
      } else if (nlQuery.includes('month')) {
        temporal.value = ['NOW() - INTERVAL \'30 days\'', 'NOW()'];
      } else if (nlQuery.includes('year')) {
        temporal.value = ['NOW() - INTERVAL \'365 days\'', 'NOW()'];
      }
    }

    return temporal;
  }

  /**
   * Extract entities from the query
   * @private
   */
  _extractEntities(nlQuery) {
    const entities = [];
    const commonEntities = [
      { type: 'status', keywords: ['open', 'closed', 'pending'], column: 'status' },
      { type: 'priority', keywords: ['high', 'medium', 'low'], column: 'priority' },
      { type: 'category', keywords: ['bug', 'feature', 'support'], column: 'category' }
    ];

    for (const entity of commonEntities) {
      for (const keyword of entity.keywords) {
        if (nlQuery.toLowerCase().includes(keyword)) {
          entities.push({
            entity_type: entity.type,
            entity_value: keyword,
            mapped_column: entity.column
          });
        }
      }
    }

    return entities;
  }

  /**
   * Find the most relevant table based on query components
   * @private
   */
  _findRelevantTable(queryComponents, tables, dbSchema) {
    // Look for table names in the query
    const nlQuery = queryComponents.context.description.toLowerCase();
    for (const table of tables) {
      if (nlQuery.includes(table.toLowerCase()) || 
          nlQuery.includes(table.slice(0, -1).toLowerCase()) || // singular form
          nlQuery.includes(table.toLowerCase() + 's')) { // plural form
        return table;
      }
    }

    // If no direct match, try to infer from entities
    for (const entity of queryComponents.entity_extraction) {
      for (const table of tables) {
        const columns = dbSchema[table].columns.map(col => col.column_name);
        if (columns.includes(entity.mapped_column)) {
          return table;
        }
      }
    }

    // Default to the first table if no match found
    return tables[0];
  }

  /**
   * Build the SQL query using decomposed components
   * @private
   */
  _buildSQLQuery(table, columns, queryComponents, dbSchema) {
    let sql = '';
    const { intent, temporal_filtering, entity_extraction } = queryComponents;

    // Handle different types of queries based on intent
    if (intent.goal === 'count_records') {
      sql = `SELECT COUNT(*) as count FROM ${table}`;
    } else if (intent.goal === 'aggregate_records') {
      // Find numeric columns for aggregation
      const numericColumns = dbSchema[table].columns
        .filter(col => ['integer', 'numeric', 'decimal'].includes(col.data_type.toLowerCase()))
        .map(col => col.column_name);
      
      if (numericColumns.length > 0) {
        sql = `SELECT AVG(${numericColumns[0]}) as average FROM ${table}`;
      } else {
        sql = `SELECT * FROM ${table}`;
      }
    } else {
      sql = `SELECT ${columns.join(', ')} FROM ${table}`;
    }

    // Add WHERE clause for filtering
    const conditions = [];

    // Add entity conditions
    for (const entity of entity_extraction) {
      conditions.push(`${entity.mapped_column} = '${entity.entity_value}'`);
    }

    // Add temporal conditions
    if (temporal_filtering.conditional_statement && temporal_filtering.value[0]) {
      const [start, end] = temporal_filtering.value;
      conditions.push(`created_at BETWEEN ${start} AND ${end}`);
    }

    if (conditions.length > 0) {
      sql += ` WHERE ${conditions.join(' AND ')}`;
    }

    // Add LIMIT by default for retrieve queries
    if (intent.goal === 'retrieve_records') {
      sql += ' LIMIT 100';
    }

    return sql;
  }
}

module.exports = new Text2SQLService();