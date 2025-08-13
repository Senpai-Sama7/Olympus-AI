import User from '../models/User.js';
import logger from '../utils/logger.js';

// @desc    Register user
// @route   POST /api/auth/register
// @access  Public
export const register = async (req, res, next) => {
  try {
    const { name, email, password } = req.body;

    // Check if user exists
    const userExists = await User.findOne({ email });
    if (userExists) {
      return res.status(400).json({
        success: false,
        data: null,
        message: 'User already exists'
      });
    }

    // Create user
    const user = await User.create({
      name,
      email,
      password
    });

    // Create token
    const token = user.getSignedJwtToken();

    logger.info(`New user registered: ${user.email}`);

    res.status(201).json({
      success: true,
      data: {
        token,
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          role: user.role
        }
      },
      message: 'User registered successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Login user
// @route   POST /api/auth/login
// @access  Public
export const login = async (req, res, next) => {
  try {
    const { email, password } = req.body;

    // Check for user
    const user = await User.findOne({ email }).select('+password +loginAttempts +lockUntil');

    if (!user) {
      return res.status(401).json({
        success: false,
        data: null,
        message: 'Invalid credentials'
      });
    }

    // Check if account is locked
    if (user.isLocked) {
      return res.status(423).json({
        success: false,
        data: null,
        message: 'Account is locked due to too many failed login attempts. Please try again later.'
      });
    }

    // Check if password matches
    const isMatch = await user.comparePassword(password);

    if (!isMatch) {
      await user.incLoginAttempts();
      return res.status(401).json({
        success: false,
        data: null,
        message: 'Invalid credentials'
      });
    }

    // Reset login attempts on successful login
    if (user.loginAttempts > 0) {
      await user.resetLoginAttempts();
    }

    // Update last login
    user.lastLogin = Date.now();
    await user.save();

    // Create tokens
    const token = user.getSignedJwtToken();
    const refreshToken = await user.generateRefreshToken();

    logger.info(`User logged in: ${user.email}`);

    res.status(200).json({
      success: true,
      data: {
        token,
        refreshToken,
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          role: user.role
        }
      },
      message: 'Login successful'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Refresh token
// @route   POST /api/auth/refresh
// @access  Public
export const refreshToken = async (req, res, next) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({
        success: false,
        data: null,
        message: 'Refresh token is required'
      });
    }

    // Find user with this refresh token
    const user = await User.findOne({ 'refreshTokens.token': refreshToken });

    if (!user || !user.validateRefreshToken(refreshToken)) {
      return res.status(401).json({
        success: false,
        data: null,
        message: 'Invalid refresh token'
      });
    }

    // Remove old refresh token
    await user.removeRefreshToken(refreshToken);

    // Generate new tokens
    const newToken = user.getSignedJwtToken();
    const newRefreshToken = await user.generateRefreshToken();

    logger.info(`Token refreshed for user: ${user.email}`);

    res.status(200).json({
      success: true,
      data: {
        token: newToken,
        refreshToken: newRefreshToken,
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          role: user.role
        }
      },
      message: 'Token refreshed successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get current logged in user
// @route   GET /api/auth/me
// @access  Private
export const getMe = async (req, res, next) => {
  try {
    const user = await User.findById(req.user.id);

    res.status(200).json({
      success: true,
      data: { user },
      message: 'User fetched successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Update password
// @route   PUT /api/auth/updatepassword
// @access  Private
export const updatePassword = async (req, res, next) => {
  try {
    const user = await User.findById(req.user.id).select('+password');

    // Check current password
    if (!(await user.comparePassword(req.body.currentPassword))) {
      return res.status(401).json({
        success: false,
        data: null,
        message: 'Password is incorrect'
      });
    }

    user.password = req.body.newPassword;
    await user.save();

    const token = user.getSignedJwtToken();

    logger.info(`Password updated for user: ${user.email}`);

    res.status(200).json({
      success: true,
      data: { token },
      message: 'Password updated successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Logout user / clear cookie
// @route   POST /api/auth/logout
// @access  Private
export const logout = async (req, res, next) => {
  try {
    res.status(200).json({
      success: true,
      data: {},
      message: 'Logged out successfully'
    });
  } catch (error) {
    next(error);
  }
};
