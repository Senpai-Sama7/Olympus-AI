import compression from 'compression';
import cors from 'cors';
import express from 'express';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import swaggerUi from 'swagger-ui-express';
import errorHandler from './middleware/errorHandler.js';
import { createAdvancedRateLimiter, requestId, sanitizeInput, securityHeaders } from './middleware/security.js';
import adminRoutes from './routes/admin.js';
import authRoutes from './routes/auth.js';
import productRoutes from './routes/product.js';
import userRoutes from './routes/user.js';
import cacheService from './services/cache.service.js';
import logger from './utils/logger.js';
import { swaggerSpec } from './utils/swagger.js';

const app = express();

// Request ID middleware (first to track all requests)
app.use(requestId);

// Security middleware
app.use(helmet());
app.use(securityHeaders);

// Optional Redis-backed rate limiter (IP-based)
if (process.env.REDIS_URL) {
  try {
    const { default: IORedis } = await import('ioredis');
    const redisClient = new IORedis(process.env.REDIS_URL);
    app.use(createAdvancedRateLimiter(redisClient));
    await cacheService.initRedis(redisClient);
    logger.info('Advanced rate limiter enabled with Redis');
  } catch (e) {
    logger.warn('Failed to initialize Redis rate limiter; continuing without it. Reason:', e?.message || e);
  }
}

// CORS configuration
app.use(cors({
  origin: process.env.NODE_ENV === 'production'
    ? process.env.FRONTEND_URL
    : ['http://localhost:3000', 'http://localhost:5173'],
  credentials: true
}));

// Compression middleware
app.use(compression());

// Body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Input sanitization (after body parsing)
app.use(sanitizeInput);

// Basic rate limiting for /api as a fallback when Redis is not configured
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 200, // Limit each IP to 200 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

// Request logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info({
      method: req.method,
      url: req.url,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip
    });
  });
  next();
});

// API Documentation
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    success: true,
    data: {
      status: 'healthy',
      uptime: process.uptime(),
      timestamp: new Date().toISOString()
    },
    message: 'Server is healthy'
  });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/products', productRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    data: null,
    message: 'Resource not found'
  });
});

// Global error handler
app.use(errorHandler);

export default app;
