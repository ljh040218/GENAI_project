// models/RefreshToken.js
const db = require('../config/database');

class RefreshToken {
  // 유저당 1개의 리프레시 토큰만 유지 (user_id UNIQUE 기준)
  static async saveToken(userId, token) {
    try {
      const query = `
        INSERT INTO refresh_tokens (user_id, token)
        VALUES ($1, $2)
        ON CONFLICT (user_id)
        DO UPDATE SET token = EXCLUDED.token, created_at = CURRENT_TIMESTAMP;
      `;
      await db.query(query, [userId, token]);
    } catch (err) {
      console.error('Error saving refresh token:', err);
      throw err;
    }
  }

  static async findByToken(token) {
    try {
      const query = 'SELECT * FROM refresh_tokens WHERE token = $1';
      const result = await db.query(query, [token]);
      return result.rows[0];
    } catch (err) {
      console.error('Error finding refresh token:', err);
      throw err;
    }
  }

  static async deleteToken(token) {
    try {
      const query = 'DELETE FROM refresh_tokens WHERE token = $1';
      await db.query(query, [token]);
    } catch (err) {
      console.error('Error deleting refresh token:', err);
      throw err;
    }
  }
}

module.exports = RefreshToken;
