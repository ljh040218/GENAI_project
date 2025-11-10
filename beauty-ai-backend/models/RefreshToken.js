// models/RefreshToken.js
const db = require('../config/database');

class RefreshToken {
  static async saveToken(userId, token) {
    try {
      await db.query(
        `
        INSERT INTO refresh_tokens (user_id, token)
        VALUES ($1, $2)
        ON CONFLICT (user_id)
        DO UPDATE SET token = EXCLUDED.token, created_at = CURRENT_TIMESTAMP;
        `,
        [userId, token]
      );
    } catch (err) {
      console.error('Error saving refresh token:', err.message);
      throw err;
    }
  }

  static async findByToken(token) {
    try {
      const result = await db.query(
        'SELECT * FROM refresh_tokens WHERE token = $1',
        [token]
      );
      return result.rows[0];
    } catch (err) {
      console.error('Error finding refresh token:', err.message);
      throw err;
    }
  }

  static async deleteToken(token) {
    try {
      await db.query('DELETE FROM refresh_tokens WHERE token = $1', [token]);
    } catch (err) {
      console.error('Error deleting refresh token:', err.message);
      throw err;
    }
  }
}

module.exports = RefreshToken;
