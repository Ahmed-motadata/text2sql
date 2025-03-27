const databaseService = require('../services/database.service');

class DatabaseController {
  async getTables(req, res) {
    try {
      const tables = await databaseService.getTables();
      res.json({ success: true, tables });
    } catch (error) {
      console.error('Error in getTables:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to fetch tables'
      });
    }
  }

  async testConnection(req, res) {
    try {
      console.log('Testing database connection...');
      const health = await databaseService.healthCheck();
      console.log('Health check result:', health);
      
      if (health.status === 'connected') {
        res.json({ success: true, message: 'Database connected successfully' });
      } else {
        res.status(500).json({
          success: false,
          error: health.message || 'Database connection failed',
          details: health
        });
      }
    } catch (error) {
      console.error('Error in testConnection:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to connect to database',
        details: {
          code: error.code,
          errno: error.errno,
          sqlState: error.sqlState
        }
      });
    }
  }

  async executeSQL(req, res) {
    try {
      const { query } = req.body;
      if (!query) {
        return res.status(400).json({
          success: false,
          error: 'Query is required'
        });
      }

      const result = await databaseService.executeQuery(query);
      res.json({ success: true, result });
    } catch (error) {
      console.error('Error in executeSQL:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to execute query'
      });
    }
  }

  async getSchemaInfo(req, res) {
    try {
      const schemaInfo = await databaseService.getSchemaInfo();
      res.json({ success: true, schemaInfo });
    } catch (error) {
      console.error('Error in getSchemaInfo:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to fetch schema information'
      });
    }
  }

  async getQueryPage(req, res) {
    try {
      const { queryId, page } = req.params;
      const pageData = await databaseService.getQueryPage(queryId, page);
      res.json({ success: true, pageData });
    } catch (error) {
      console.error('Error in getQueryPage:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to fetch query page'
      });
    }
  }

  async disconnect(req, res) {
    try {
      await databaseService.disconnect();
      res.json({ success: true, message: 'Successfully disconnected from database' });
    } catch (error) {
      console.error('Error in disconnect:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to disconnect from database'
      });
    }
  }
}

module.exports = new DatabaseController();