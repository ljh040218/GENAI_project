// controllers/authController.js
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const RefreshToken = require('../models/RefreshToken');
require('dotenv').config();

const generateTokens = (user) => {
  const accessToken = jwt.sign(
    { id: user.id, email: user.email },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRE || '7d' }
  );

  const refreshToken = jwt.sign(
    { id: user.id },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_REFRESH_EXPIRE || '30d' }
  );

  return { accessToken, refreshToken };
};

exports.register = async (req, res) => {
  try {
    const { username, email, password } = req.body;

    if (!username || !email || !password) {
      return res.status(400).json({ success: false, message: 'All fields are required' });
    }

    const emailExists = await User.checkEmailExists(email);
    if (emailExists) {
      return res.status(400).json({ success: false, message: 'Email already registered' });
    }

    const usernameExists = await User.checkUsernameExists(username);
    if (usernameExists) {
      return res.status(400).json({ success: false, message: 'Username already taken' });
    }

    const user = await User.create({ username, email, password });
    const tokens = generateTokens(user);

    await RefreshToken.saveToken(user.id, tokens.refreshToken);

    res.status(201).json({
      success: true,
      message: 'User registered successfully',
      user,
      ...tokens
    });
  } catch (error) {
    console.error('❌ Register error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
};

exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ success: false, message: 'Email and password are required' });
    }

    const user = await User.findByEmail(email);

    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    if (!user.password_hash) {
      console.error('⚠️ password_hash is missing for user:', email);
      return res.status(500).json({ success: false, message: 'User data corrupted' });
    }

    const validPassword = await User.verifyPassword(password, user.password_hash);

    if (!validPassword) {
      return res.status(401).json({ success: false, message: 'Invalid password' });
    }

    const tokens = generateTokens(user);
    await RefreshToken.saveToken(user.id, tokens.refreshToken);

    await User.updateLastLogin(user.id);

    res.status(200).json({
      success: true,
      message: 'Login successful',
      user: {
        id: user.id,
        username: user.username,
        email: user.email
      },
      ...tokens
    });
  } catch (error) {
    console.error('❌ Login error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
};

exports.refreshToken = async (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({ success: false, message: 'No refresh token provided' });
    }

    const tokenRecord = await RefreshToken.findByToken(refreshToken);

    if (!tokenRecord) {
      return res.status(403).json({ success: false, message: 'Invalid refresh token' });
    }

    const decoded = jwt.verify(refreshToken, process.env.JWT_SECRET);
    const user = await User.findById(decoded.id);

    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    const tokens = generateTokens(user);
    await RefreshToken.saveToken(user.id, tokens.refreshToken);

    res.status(200).json({
      success: true,
      message: 'Token refreshed successfully',
      ...tokens
    });
  } catch (error) {
    console.error('❌ Refresh token error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
};

exports.logout = async (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({ success: false, message: 'Refresh token required' });
    }

    await RefreshToken.deleteToken(refreshToken);
    res.status(200).json({ success: true, message: 'Logged out successfully' });
  } catch (error) {
    console.error('❌ Logout error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
};

exports.getProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user.id);

    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    res.status(200).json({ success: true, user });
  } catch (error) {
    console.error('❌ Get profile error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
};
