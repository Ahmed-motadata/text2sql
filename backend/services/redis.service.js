const Redis = require('ioredis');

class RedisService {
  constructor() {
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      maxRetriesPerRequest: null,
    });

    // Default TTL for query results (1 hour)
    this.DEFAULT_TTL = 3600;

    // Test Redis connection
    this.redis.on('connect', () => {
      console.log('Redis connected successfully');
    });

    this.redis.on('error', (error) => {
      console.error('Redis connection error:', error);
    });
  }

  async set(key, value) {
    try {
      console.log('Storing data in Redis for key:', key);
      console.log('Data size:', JSON.stringify(value).length, 'bytes');
      await this.redis.setex(key, this.DEFAULT_TTL, value);
      console.log('Successfully stored data in Redis');
      return true;
    } catch (error) {
      console.error('Redis set error:', error);
      throw error;
    }
  }

  async get(key) {
    try {
      console.log('Retrieving data from Redis for key:', key);
      const data = await this.redis.get(key);
      if (!data) {
        console.log('No data found in Redis for key:', key);
      } else {
        console.log('Successfully retrieved data from Redis');
        console.log('Data size:', data.length, 'bytes');
      }
      return data;
    } catch (error) {
      console.error('Redis get error:', error);
      throw error;
    }
  }

  async del(key) {
    try {
      console.log('Deleting data from Redis for key:', key);
      await this.redis.del(key);
      console.log('Successfully deleted data from Redis');
      return true;
    } catch (error) {
      console.error('Redis delete error:', error);
      throw error;
    }
  }
}

module.exports = new RedisService();