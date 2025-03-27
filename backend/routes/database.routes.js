const express = require('express');
const router = express.Router();
const databaseController = require('../controllers/database.controller');

// Test database connection
router.get('/test-connection', databaseController.testConnection);

// Get all tables
router.get('/tables', databaseController.getTables);

// Get schema information
router.get('/schema-info', databaseController.getSchemaInfo);

// Execute SQL query
router.post('/execute', databaseController.executeSQL);

// Get paginated query results
router.get('/query-results/:queryId/:page', databaseController.getQueryPage);

// Disconnect from database
router.post('/disconnect', databaseController.disconnect);

module.exports = router;