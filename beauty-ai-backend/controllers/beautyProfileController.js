const pool = require('../config/database');
const { validationResult } = require('express-validator');

exports.createBeautyProfile = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      message: 'Validation failed',
      errors: errors.array()
    });
  }

  const client = await pool.connect();
  
  try {
    const {
      personalColor,
      skinUndertone,
      skinType,
      contrastLevel,
      preferredFinish,
      preferredStore,
      priceRangeMin,
      priceRangeMax,
      preferences
    } = req.body;
    
    const userId = req.user.id;

    if (!personalColor || !skinUndertone) {
      return res.status(400).json({
        success: false,
        message: 'personalColor and skinUndertone are required'
      });
    }

    const existingProfile = await client.query(
      'SELECT * FROM beauty_profiles WHERE user_id = $1',
      [userId]
    );

    if (existingProfile.rows.length > 0) {
      return res.status(400).json({
        success: false,
        message: 'Beauty profile already exists. Use PUT to update.'
      });
    }

    const result = await client.query(
      `INSERT INTO beauty_profiles (
        user_id, personal_color, skin_undertone, skin_type, 
        contrast_level, preferred_finish, preferred_store, 
        price_range_min, price_range_max, preferences
      )
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
       RETURNING *`,
      [
        userId, 
        personalColor, 
        skinUndertone, 
        skinType || null,
        contrastLevel || null, 
        preferredFinish || null,
        preferredStore || null,
        priceRangeMin || null, 
        priceRangeMax || null,
        preferences ? JSON.stringify(preferences) : '{}'
      ]
    );

    res.status(201).json({
      success: true,
      message: 'Beauty profile created successfully',
      profile: result.rows[0]
    });

  } catch (error) {
    console.error('Create profile error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error',
      error: error.message
    });
  } finally {
    client.release();
  }
};

exports.getBeautyProfile = async (req, res) => {
  const client = await pool.connect();
  
  try {
    const userId = req.user.id;

    const result = await client.query(
      'SELECT * FROM beauty_profiles WHERE user_id = $1',
      [userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Beauty profile not found'
      });
    }

    res.json({
      success: true,
      profile: result.rows[0]
    });

  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error'
    });
  } finally {
    client.release();
  }
};

exports.updateBeautyProfile = async (req, res) => {
  const client = await pool.connect();
  
  try {
    const {
      personalColor,
      skinUndertone,
      skinType,
      contrastLevel,
      preferredFinish,
      preferredStore,
      priceRangeMin,
      priceRangeMax,
      preferences
    } = req.body;
    
    const userId = req.user.id;

    const updates = [];
    const values = [];
    let paramCount = 1;

    if (personalColor !== undefined) {
      updates.push(`personal_color = $${paramCount}`);
      values.push(personalColor);
      paramCount++;
    }
    if (skinUndertone !== undefined) {
      updates.push(`skin_undertone = $${paramCount}`);
      values.push(skinUndertone);
      paramCount++;
    }
    if (skinType !== undefined) {
      updates.push(`skin_type = $${paramCount}`);
      values.push(skinType || null);
      paramCount++;
    }
    if (contrastLevel !== undefined) {
      updates.push(`contrast_level = $${paramCount}`);
      values.push(contrastLevel || null);
      paramCount++;
    }
    if (preferredFinish !== undefined) {
      updates.push(`preferred_finish = $${paramCount}`);
      values.push(preferredFinish || null);
      paramCount++;
    }
    if (preferredStore !== undefined) {
      updates.push(`preferred_store = $${paramCount}`);
      values.push(preferredStore || null);
      paramCount++;
    }
    if (priceRangeMin !== undefined) {
      updates.push(`price_range_min = $${paramCount}`);
      values.push(priceRangeMin || null);
      paramCount++;
    }
    if (priceRangeMax !== undefined) {
      updates.push(`price_range_max = $${paramCount}`);
      values.push(priceRangeMax || null);
      paramCount++;
    }
    if (preferences !== undefined) {
      updates.push(`preferences = $${paramCount}`);
      values.push(JSON.stringify(preferences));
      paramCount++;
    }

    if (updates.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'No fields to update'
      });
    }

    values.push(userId);

    const query = `
      UPDATE beauty_profiles 
      SET ${updates.join(', ')}, updated_at = NOW()
      WHERE user_id = $${paramCount}
      RETURNING *
    `;

    const result = await client.query(query, values);

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Beauty profile not found'
      });
    }

    res.json({
      success: true,
      message: 'Profile updated successfully',
      profile: result.rows[0]
    });

  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error'
    });
  } finally {
    client.release();
  }
};