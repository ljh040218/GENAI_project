const express = require('express');
const router = express.Router();
const multer = require('multer');
const axios = require('axios');
const pool = require('../config/database');
const authMiddleware = require('../middleware/authMiddleware');

const upload = multer({ storage: multer.memoryStorage() });
router.post('/agent/chat', authMiddleware, async (req, res) => {
  try {
    const { message, currentRecommendations, category } = req.body;
    const userId = req.user.id;

    if (!message || !currentRecommendations || !category) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: message, currentRecommendations, category'
      });
    }

    const profileResult = await pool.query(
      'SELECT * FROM beauty_profiles WHERE user_id = $1',
      [userId]
    );

    const userProfile = profileResult.rows.length > 0 ? {
      personal_color: profileResult.rows[0].personal_color,
      skin_undertone: profileResult.rows[0].skin_undertone,
      skin_type: profileResult.rows[0].skin_type,
      contrast_level: profileResult.rows[0].contrast_level,
      preferred_finish: profileResult.rows[0].preferred_finish,
      preferred_store: profileResult.rows[0].preferred_store,
      price_range_min: profileResult.rows[0].price_range_min,
      price_range_max: profileResult.rows[0].price_range_max,
      preferences: profileResult.rows[0].preferences
    } : {};

    const response = await axios.post(
      `${process.env.PYTHON_API_URL}/api/agent/message`,
      {
        user_id: userId,
        message: message,
        current_recommendations: currentRecommendations,
        user_profile: userProfile,
        category: category
      },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000
      }
    );

    res.json(response.data);
  } catch (error) {
    console.error('Agent chat error:', error.response?.data || error.message);
    res.status(500).json({
      success: false,
      error: error.response?.data?.detail || error.message
    });
  }
});

router.get('/agent/history/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const { category, limit = 10 } = req.query;

    const query = `
      SELECT feedback_id, user_id, text, metadata, created_at
      FROM feedback_embeddings
      WHERE user_id = $1
      ${category ? 'AND metadata->>\'category\' = $2' : ''}
      ORDER BY created_at DESC
      LIMIT $${category ? 3 : 2}
    `;

    const params = category ? [userId, category, limit] : [userId, limit];
    const result = await pool.query(query, params);

    res.json({
      success: true,
      history: result.rows
    });
  } catch (error) {
    console.error('Get history error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});