const db = require('../config/database');

class RefreshToken {
  static async create(userId, token, expiresAt) {
    const query = `
      INSERT INTO refresh_tokens (user_id, token, expires_at)
      VALUES ($1, $2, $3)
      RETURNING id, token, expires_at
    `;
    
    const result = await db.query(query, [userId, token, expiresAt]);
    return result.rows[0];
  }

  static async findByToken(token) {
    const query = `
      SELECT * FROM refresh_tokens 
      WHERE token = $1 AND revoked = false AND expires_at > CURRENT_TIMESTAMP
    `;
    const result = await db.query(query, [token]);
    return result.rows[0];
  }

  static async revokeToken(token) {
    const query = 'UPDATE refresh_tokens SET revoked = true WHERE token = $1';
    await db.query(query, [token]);
  }

  static async revokeAllUserTokens(userId) {
    const query = 'UPDATE refresh_tokens SET revoked = true WHERE user_id = $1';
    await db.query(query, [userId]);
  }

  static async deleteExpiredTokens() {
    const query = 'DELETE FROM refresh_tokens WHERE expires_at < CURRENT_TIMESTAMP';
    await db.query(query);
  }
}

module.exports = RefreshToken;
