import NodeCache from 'node-cache';
import logger from '../utils/logger.js';

class CacheService {
  constructor() {
    // In-memory cache with 5-minute default TTL
    this.memoryCache = new NodeCache({
      stdTTL: 300,
      checkperiod: 60,
      useClones: false
    });

    this.redisClient = null;
    this.isRedisConnected = false;
  }

  // Initialize Redis connection (optional)
  async initRedis(redisClient) {
    try {
      this.redisClient = redisClient;
      await this.redisClient.ping();
      this.isRedisConnected = true;
      logger.info('Redis cache initialized successfully');
    } catch (error) {
      logger.warn('Redis cache initialization failed, falling back to memory cache:', error.message);
      this.isRedisConnected = false;
    }
  }

  // Get from cache
  async get(key) {
    try {
      // Try Redis first if available
      if (this.isRedisConnected && this.redisClient) {
        const value = await this.redisClient.get(key);
        if (value) {
          return JSON.parse(value);
        }
      }

      // Fall back to memory cache
      return this.memoryCache.get(key);
    } catch (error) {
      logger.error('Cache get error:', error);
      return null;
    }
  }

  // Set cache value
  async set(key, value, ttl = 300) {
    try {
      // Set in memory cache
      this.memoryCache.set(key, value, ttl);

      // Also set in Redis if available
      if (this.isRedisConnected && this.redisClient) {
        await this.redisClient.setex(key, ttl, JSON.stringify(value));
      }

      return true;
    } catch (error) {
      logger.error('Cache set error:', error);
      return false;
    }
  }

  // Delete from cache
  async del(key) {
    try {
      // Delete from memory cache
      this.memoryCache.del(key);

      // Also delete from Redis if available
      if (this.isRedisConnected && this.redisClient) {
        await this.redisClient.del(key);
      }

      return true;
    } catch (error) {
      logger.error('Cache delete error:', error);
      return false;
    }
  }

  // Clear all cache
  async flush() {
    try {
      // Clear memory cache
      this.memoryCache.flushAll();

      // Also clear Redis if available
      if (this.isRedisConnected && this.redisClient) {
        await this.redisClient.flushdb();
      }

      return true;
    } catch (error) {
      logger.error('Cache flush error:', error);
      return false;
    }
  }

  // Cache middleware for Express routes
  middleware(keyGenerator, ttl = 300) {
    return async (req, res, next) => {
      // Skip caching for non-GET requests
      if (req.method !== 'GET') {
        return next();
      }

      const key = typeof keyGenerator === 'function'
        ? keyGenerator(req)
        : `${req.originalUrl || req.url}`;

      try {
        const cachedData = await this.get(key);

        if (cachedData) {
          logger.debug(`Cache hit for key: ${key}`);
          return res.json(cachedData);
        }

        // Store original json method
        const originalJson = res.json;

        // Override json method to cache the response
        res.json = (data) => {
          // Only cache successful responses
          if (res.statusCode >= 200 && res.statusCode < 300) {
            this.set(key, data, ttl).catch(err =>
              logger.error('Failed to cache response:', err)
            );
          }

          // Call original json method
          return originalJson.call(res, data);
        };

        next();
      } catch (error) {
        logger.error('Cache middleware error:', error);
        next();
      }
    };
  }

  // Get cache stats
  getStats() {
    const memoryStats = this.memoryCache.getStats();

    return {
      memory: {
        keys: this.memoryCache.keys().length,
        hits: memoryStats.hits,
        misses: memoryStats.misses,
        ksize: memoryStats.ksize,
        vsize: memoryStats.vsize
      },
      redis: {
        connected: this.isRedisConnected
      }
    };
  }
}

// Export singleton instance
export default new CacheService();

