// Test database connection endpoint
const express = require('express');
const router = express.Router();
const databaseService = require('../services/database.service');

router.get('/test-connection', async (req, res) => {
  try {
    // Attempt to fetch tables to verify connection
    const tables = await databaseService.getTables();
    res.json({ success: true, message: 'Database connection successful', tables });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to connect to database', error: error.message });
  }
});

// Test specific database connection endpoint
router.get('/connect', async (req, res) => {
  try {
    await databaseService.connect();
    const tables = await databaseService.getTables();
    res.json({ 
      success: true, 
      message: 'Database connection successful',
      tables 
    });
  } catch (error) {
    console.error('Connection test error:', error);
    res.status(500).json({ 
      success: false, 
      error: error.message || 'Failed to connect to database'
    });
  }
});

module.exports = router;