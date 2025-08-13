import Joi from 'joi';

export const validate = (schema) => {
  return (req, res, next) => {
    const { error } = schema.validate(req.body, { abortEarly: false });

    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));

      return res.status(400).json({
        success: false,
        data: null,
        message: 'Validation error',
        errors
      });
    }

    next();
  };
};

// Auth validation schemas
export const registerSchema = Joi.object({
  name: Joi.string().min(2).max(50).required(),
  email: Joi.string().email().required(),
  password: Joi.string().min(6).required()
});

export const loginSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().required()
});

export const updatePasswordSchema = Joi.object({
  currentPassword: Joi.string().required(),
  newPassword: Joi.string().min(6).required()
});

// User validation schemas
export const updateUserSchema = Joi.object({
  name: Joi.string().min(2).max(50),
  email: Joi.string().email()
}).min(1);

// Product validation schemas
export const createProductSchema = Joi.object({
  name: Joi.string().min(2).max(100).required(),
  description: Joi.string().max(500),
  price: Joi.number().min(0).required(),
  category: Joi.string().valid('electronics', 'clothing', 'food', 'books', 'toys', 'other').required(),
  quantity: Joi.number().integer().min(0).default(0),
  images: Joi.array().items(Joi.string().uri()),
  tags: Joi.array().items(Joi.string())
});

export const updateProductSchema = Joi.object({
  name: Joi.string().min(2).max(100),
  description: Joi.string().max(500),
  price: Joi.number().min(0),
  category: Joi.string().valid('electronics', 'clothing', 'food', 'books', 'toys', 'other'),
  quantity: Joi.number().integer().min(0),
  inStock: Joi.boolean(),
  images: Joi.array().items(Joi.string().uri()),
  tags: Joi.array().items(Joi.string())
}).min(1);

// Query validation schemas
export const paginationSchema = Joi.object({
  page: Joi.number().integer().min(1).default(1),
  limit: Joi.number().integer().min(1).max(100).default(10),
  sort: Joi.string().default('-createdAt'),
  fields: Joi.string()
});

export const productQuerySchema = paginationSchema.keys({
  category: Joi.string().valid('electronics', 'clothing', 'food', 'books', 'toys', 'other'),
  minPrice: Joi.number().min(0),
  maxPrice: Joi.number().min(0),
  inStock: Joi.boolean(),
  search: Joi.string()
});
