const db = require('../config/database');

class RefreshToken {
  static async saveToken(userId, token, expiresAt) {
    const query = `
      INSERT INTO refresh_tokens (user_id, token, expires_at)
      VALUES ($1, $2, $3)
      ON CONFLICT (user_id)
      DO UPDATE SET token = EXCLUDED.token, expires_at = EXCLUDED.expires_at;
    `;
    await db.query(query, [userId, token, expiresAt]);
  }

  static async findByToken(token) {
    const query = 'SELECT * FROM refresh_tokens WHERE token = $1';
    const result = await db.query(query, [token]);
    return result.rows[0];
  }

  static async deleteByUserId(userId) {
    const query = 'DELETE FROM refresh_tokens WHERE user_id = $1';
    await db.query(query, [userId]);
  }
}

module.exports = RefreshToken;
