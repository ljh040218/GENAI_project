const User = require('../models/User');
const RefreshToken = require('../models/RefreshToken');
const { generateAccessToken, generateRefreshToken, verifyToken } = require('../utils/jwt');

class AuthController {
  static async register(req, res) {
    try {
      const { username, email, password } = req.body;

      const emailExists = await User.checkEmailExists(email);
      if (emailExists) {
        return res.status(400).json({
          success: false,
          message: 'Email already registered'
        });
      }

      const usernameExists = await User.checkUsernameExists(username);
      if (usernameExists) {
        return res.status(400).json({
          success: false,
          message: 'Username already taken'
        });
      }

      const user = await User.create({ username, email, password });

      const accessToken = generateAccessToken(user.id, user.username);
      const refreshToken = generateRefreshToken(user.id);

      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + 30);
      await RefreshToken.create(user.id, refreshToken, expiresAt);

      return res.status(201).json({
        success: true,
        message: 'User registered successfully',
        data: {
          user: {
            id: user.id,
            username: user.username,
            email: user.email
          },
          tokens: {
            accessToken,
            refreshToken
          }
        }
      });
    } catch (error) {
      console.error('Registration error:', error);
      return res.status(500).json({
        success: false,
        message: 'Internal server error'
      });
    }
  }

  static async login(req, res) {
    try {
      const { email, password } = req.body;

      const user = await User.findByEmail(email);
      if (!user) {
        return res.status(401).json({
          success: false,
          message: 'Invalid email or password'
        });
      }

      if (!user.is_active) {
        return res.status(403).json({
          success: false,
          message: 'Account is deactivated'
        });
      }

      const isPasswordValid = await User.verifyPassword(password, user.password_hash);
      if (!isPasswordValid) {
        return res.status(401).json({
          success: false,
          message: 'Invalid email or password'
        });
      }

      await User.updateLastLogin(user.id);

      const accessToken = generateAccessToken(user.id, user.username);
      const refreshToken = generateRefreshToken(user.id);

      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + 30);
      await RefreshToken.create(user.id, refreshToken, expiresAt);

      return res.status(200).json({
        success: true,
        message: 'Login successful',
        data: {
          user: {
            id: user.id,
            username: user.username,
            email: user.email
          },
          tokens: {
            accessToken,
            refreshToken
          }
        }
      });
    } catch (error) {
      console.error('Login error:', error);
      return res.status(500).json({
        success: false,
        message: 'Internal server error'
      });
    }
  }

  static async refreshToken(req, res) {
    try {
      const { refreshToken } = req.body;

      if (!refreshToken) {
        return res.status(400).json({
          success: false,
          message: 'Refresh token is required'
        });
      }

      const decoded = verifyToken(refreshToken);
      
      const tokenRecord = await RefreshToken.findByToken(refreshToken);
      if (!tokenRecord) {
        return res.status(401).json({
          success: false,
          message: 'Invalid or expired refresh token'
        });
      }

      const user = await User.findById(decoded.userId);
      if (!user || !user.is_active) {
        return res.status(401).json({
          success: false,
          message: 'User not found or inactive'
        });
      }

      await RefreshToken.revokeToken(refreshToken);

      const newAccessToken = generateAccessToken(user.id, user.username);
      const newRefreshToken = generateRefreshToken(user.id);

      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + 30);
      await RefreshToken.create(user.id, newRefreshToken, expiresAt);

      return res.status(200).json({
        success: true,
        message: 'Token refreshed successfully',
        data: {
          tokens: {
            accessToken: newAccessToken,
            refreshToken: newRefreshToken
          }
        }
      });
    } catch (error) {
      console.error('Refresh token error:', error);
      return res.status(401).json({
        success: false,
        message: 'Invalid or expired refresh token'
      });
    }
  }

  static async logout(req, res) {
    try {
      const { refreshToken } = req.body;

      if (refreshToken) {
        await RefreshToken.revokeToken(refreshToken);
      }

      return res.status(200).json({
        success: true,
        message: 'Logout successful'
      });
    } catch (error) {
      console.error('Logout error:', error);
      return res.status(500).json({
        success: false,
        message: 'Internal server error'
      });
    }
  }

  static async getProfile(req, res) {
    try {
      const user = await User.findById(req.user.userId);
      
      if (!user) {
        return res.status(404).json({
          success: false,
          message: 'User not found'
        });
      }

      return res.status(200).json({
        success: true,
        data: {
          user: {
            id: user.id,
            username: user.username,
            email: user.email,
            createdAt: user.created_at,
            lastLogin: user.last_login,
            emailVerified: user.email_verified
          }
        }
      });
    } catch (error) {
      console.error('Get profile error:', error);
      return res.status(500).json({
        success: false,
        message: 'Internal server error'
      });
    }
  }
}

module.exports = AuthController;
