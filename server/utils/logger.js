import { mkdir } from 'fs/promises';
import { join } from 'path';
import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';

// Resolve logs directory relative to working directory (/app in container)
const logsDir = join(process.cwd(), 'logs');
try {
  await mkdir(logsDir, { recursive: true });
} catch (error) {
  console.error('Failed to create logs directory:', error);
}

const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

const level = () => {
  const env = process.env.NODE_ENV || 'development';
  const isDevelopment = env === 'development';
  return isDevelopment ? 'debug' : 'info';
};

const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'white',
};

winston.addColors(colors);

const baseFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const consoleFormat = winston.format.combine(
  winston.format.colorize({ all: true }),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.printf((info) => {
    const msg = typeof info.message === 'object' ? JSON.stringify(info.message) : info.message;
    return `${info.timestamp} ${info.level}: ${msg}${info.stack ? '\n' + info.stack : ''}`;
  })
);

const transports = [
  new winston.transports.Console({
    format: consoleFormat,
  }),
];

if (process.env.NODE_ENV === 'production') {
  transports.push(
    new DailyRotateFile({
      level: 'error',
      dirname: logsDir,
      filename: 'error-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '14d',
      format: baseFormat,
    }),
    new DailyRotateFile({
      dirname: logsDir,
      filename: 'combined-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '14d',
      format: baseFormat,
    })
  );
}

const logger = winston.createLogger({
  level: level(),
  levels,
  transports,
  exitOnError: false,
  rejectionHandlers: [new winston.transports.Console({ format: consoleFormat })],
  exceptionHandlers: [new winston.transports.Console({ format: consoleFormat })],
});

export default logger;
