const DatabaseConnection = require('../utils/db_connection');
const dbConfig = require('../config/database');
const redisService = require('./redis.service');

class DatabaseService {
  constructor() {
    const environment = process.env.NODE_ENV || 'development';
    this.dbConnection = new DatabaseConnection(dbConfig[environment]);
    this.LARGE_RESULT_THRESHOLD = 1000; // Results larger than this will use Redis
    this.isConnected = false;
  }

  async connect() {
    if (!this.isConnected) {
      await this.dbConnection.connect();
      this.isConnected = true;
    }
    return true;
  }

  async getTables() {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      const db = this.dbConnection.getKnex();
      console.log('Fetching tables...');
      const result = await db.raw(`
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
      `);
      
      console.log('Tables fetched:', result.rows);
      return result.rows.map(row => row.table_name);
    } catch (error) {
      console.error('Error fetching tables:', error);
      throw error;
    }
  }

  async getSchemaInfo() {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      const db = this.dbConnection.getKnex();

      // Get all schemas first
      const schemasResult = await db.raw(`
        SELECT DISTINCT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name;
      `);

      const schemas = schemasResult.rows.map(row => row.schema_name);
      const schemaInfo = {};

      // Get table count for each schema
      for (const schema of schemas) {
        const tableCountResult = await db.raw(`
          SELECT COUNT(*) as table_count 
          FROM information_schema.tables 
          WHERE table_schema = ?;
        `, [schema]);

        schemaInfo[schema] = {
          tableCount: parseInt(tableCountResult.rows[0].table_count),
          tables: []
        };

        // Get tables for each schema
        const tablesResult = await db.raw(`
          SELECT table_name 
          FROM information_schema.tables 
          WHERE table_schema = ?
          ORDER BY table_name;
        `, [schema]);

        schemaInfo[schema].tables = tablesResult.rows.map(row => row.table_name);
      }

      return {
        schemaCount: schemas.length,
        schemas: schemas,
        details: schemaInfo
      };
    } catch (error) {
      console.error('Error fetching schema information:', error);
      throw error;
    }
  }

  async executeQuery(query) {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      console.log('Executing query:', query);
      const db = this.dbConnection.getKnex();
      const result = await db.raw(query);
      
      // If results are larger than threshold, store in Redis
      if (result.rows.length > this.LARGE_RESULT_THRESHOLD) {
        const queryId = Date.now().toString();
        await redisService.set(`query:${queryId}`, JSON.stringify(result.rows));
        
        return {
          isLargeResult: true,
          queryId,
          rowCount: result.rows.length
        };
      }
      
      // For small results, return directly
      return {
        isLargeResult: false,
        rows: result.rows,
        fields: result.fields.map(field => ({ name: field.name })),
        rowCount: result.rows.length
      };
    } catch (error) {
      console.error('Error executing query:', error);
      throw error;
    }
  }

  async getQueryPage(queryId, page) {
    try {
      const pageSize = 100;
      const start = page * pageSize;
      const end = start + pageSize;
      
      const result = await redisService.get(`query:${queryId}`);
      if (!result) {
        throw new Error('Query results not found');
      }
      
      const rows = JSON.parse(result);
      const totalRows = rows.length;
      const totalPages = Math.ceil(totalRows / pageSize);
      
      return {
        results: rows.slice(start, end),
        metadata: {
          totalRows,
          totalPages,
          pageSize,
          currentPage: page,
          hasNextPage: end < totalRows,
          hasPreviousPage: start > 0
        }
      };
    } catch (error) {
      console.error('Error fetching query page:', error);
      throw error;
    }
  }

  async healthCheck() {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      const db = this.dbConnection.getKnex();
      await db.raw('SELECT 1');
      return { status: 'connected', message: 'Database is connected' };
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        status: 'disconnected',
        message: error.message || 'Database connection failed',
        error: error
      };
    }
  }

  async disconnect() {
    try {
      if (this.isConnected) {
        await this.dbConnection.disconnect();
        this.isConnected = false;
        return true;
      }
      return true; // Already disconnected
    } catch (error) {
      console.error('Error disconnecting from database:', error);
      throw error;
    }
  }
}

module.exports = new DatabaseService();