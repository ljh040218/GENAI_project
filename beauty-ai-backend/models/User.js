const db = require('../config/database');
const bcrypt = require('bcrypt');

class User {
  static async create({ username, email, password }) {
    const passwordHash = await bcrypt.hash(password, 10);
    
    const query = `
      INSERT INTO users (username, email, password_hash)
      VALUES ($1, $2, $3)
      RETURNING id, username, email, created_at, is_active, email_verified
    `;
    
    const result = await db.query(query, [username, email, passwordHash]);
    return result.rows[0];
  }

  static async findByEmail(email) {
    const query = 'SELECT * FROM users WHERE email = $1';
    const result = await db.query(query, [email]);
    return result.rows[0];
  }

  static async findByUsername(username) {
    const query = 'SELECT * FROM users WHERE username = $1';
    const result = await db.query(query, [username]);
    return result.rows[0];
  }

  static async findById(id) {
    const query = 'SELECT id, username, email, created_at, updated_at, last_login, is_active, email_verified FROM users WHERE id = $1';
    const result = await db.query(query, [id]);
    return result.rows[0];
  }

  static async verifyPassword(password, passwordHash) {
    return await bcrypt.compare(password, passwordHash);
  }

  static async updateLastLogin(userId) {
    const query = 'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1';
    await db.query(query, [userId]);
  }

  static async checkEmailExists(email) {
    const query = 'SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)';
    const result = await db.query(query, [email]);
    return result.rows[0].exists;
  }

  static async checkUsernameExists(username) {
    const query = 'SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)';
    const result = await db.query(query, [username]);
    return result.rows[0].exists;
  }
}

module.exports = User;
