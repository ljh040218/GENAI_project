const db = require('../config/database');

class RefreshToken {
  // 리프레시 토큰 저장 (user_id 기준으로 1개만 유지)
  static async saveToken(userId, token) {
    try {
      const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30일 후 만료

      const query = `
        INSERT INTO refresh_tokens (user_id, token, expires_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id)
        DO UPDATE 
        SET token = EXCLUDED.token,
            expires_at = EXCLUDED.expires_at,
            created_at = CURRENT_TIMESTAMP;
      `;
      await db.query(query, [userId, token, expiresAt]);
    } catch (error) {
      console.error('Error saving refresh token:', error);
      throw error;
    }
  }

  static async findByToken(token) {
    try {
      const query = 'SELECT * FROM refresh_tokens WHERE token = $1';
      const result = await db.query(query, [token]);
      return result.rows[0];
    } catch (error) {
      console.error('Error finding refresh token:', error);
      throw error;
    }
  }

  static async deleteToken(token) {
    try {
      const query = 'DELETE FROM refresh_tokens WHERE token = $1';
      await db.query(query, [token]);
    } catch (error) {
      console.error('Error deleting refresh token:', error);
      throw error;
    }
  }
}

module.exports = RefreshToken;
