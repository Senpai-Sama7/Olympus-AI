import mongoose from 'mongoose';
import logger from '../utils/logger.js';

const connectDB = async () => {
  try {
    // Configure mongoose settings
    mongoose.set('strictQuery', false);

    const options = {
      // Connection pooling
      maxPoolSize: 10,
      minPoolSize: 2,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
      family: 4, // Use IPv4

      // Retry logic
      retryWrites: true,
      w: 'majority',
    };

    const conn = await mongoose.connect(process.env.MONGODB_URI, options);

    logger.info(`MongoDB Connected: ${conn.connection.host}`);

    // Monitor connection pool
    mongoose.connection.on('connected', () => {
      logger.info('Mongoose connected to MongoDB');
    });

    mongoose.connection.on('error', (err) => {
      logger.error('MongoDB connection error:', err);
    });

    mongoose.connection.on('disconnected', () => {
      logger.warn('MongoDB disconnected');
    });

    // Handle connection events
    mongoose.connection.on('reconnected', () => {
      logger.info('MongoDB reconnected');
    });

    mongoose.connection.on('close', () => {
      logger.info('MongoDB connection closed');
    });

    // Graceful shutdown
    process.on('SIGINT', async () => {
      try {
        await mongoose.connection.close();
        logger.info('MongoDB connection closed through app termination');
        process.exit(0);
      } catch (err) {
        logger.error('Error during MongoDB shutdown:', err);
        process.exit(1);
      }
    });

    process.on('SIGTERM', async () => {
      try {
        await mongoose.connection.close();
        logger.info('MongoDB connection closed through SIGTERM');
        process.exit(0);
      } catch (err) {
        logger.error('Error during MongoDB shutdown:', err);
        process.exit(1);
      }
    });

  } catch (error) {
    logger.error('MongoDB connection failed:', error);

    // Retry connection after 5 seconds
    if (process.env.NODE_ENV === 'production') {
      logger.info('Retrying MongoDB connection in 5 seconds...');
      setTimeout(connectDB, 5000);
    } else {
      throw error;
    }
  }
};

export default connectDB;
