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
  }

  async set(key, value) {
    try {
      await this.redis.setex(key, this.DEFAULT_TTL, value);
      return true;
    } catch (error) {
      console.error('Redis set error:', error);
      throw error;
    }
  }

  async get(key) {
    try {
      return await this.redis.get(key);
    } catch (error) {
      console.error('Redis get error:', error);
      throw error;
    }
  }

  async del(key) {
    try {
      await this.redis.del(key);
      return true;
    } catch (error) {
      console.error('Redis delete error:', error);
      throw error;
    }
  }
}

module.exports = new RedisService();