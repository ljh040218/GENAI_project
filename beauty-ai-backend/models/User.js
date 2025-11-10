const pool = require("../config/database");

class User {
  // 회원 생성
  static async create(username, email, passwordHash) {
    try {
      const res = await pool.query(
        `INSERT INTO users (username, email, password_hash)
         VALUES ($1, $2, $3)
         RETURNING id, username, email, created_at, last_login`,
        [username, email, passwordHash]
      );
      return res.rows[0];
    } catch (err) {
      console.error("User.create error:", err);
      throw err;
    }
  }

  // 이메일로 유저 조회
  static async findByEmail(email) {
    try {
      const res = await pool.query(
        `SELECT * FROM users WHERE email = $1`,
        [email]
      );
      return res.rows[0];
    } catch (err) {
      console.error("User.findByEmail error:", err);
      throw err;
    }
  }

  // 닉네임으로 유저 조회
  static async findByUsername(username) {
    try {
      const res = await pool.query(
        `SELECT * FROM users WHERE username = $1`,
        [username]
      );
      return res.rows[0];
    } catch (err) {
      console.error("User.findByUsername error:", err);
      throw err;
    }
  }

  // ID로 유저 조회 (프로필용)
  static async findById(id) {
    try {
      const res = await pool.query(
        `SELECT id, username, email, created_at, last_login
         FROM users
         WHERE id = $1`,
        [id]
      );
      return res.rows[0];
    } catch (err) {
      console.error("User.findById error:", err);
      throw err;
    }
  }

  // 마지막 로그인 갱신
  static async updateLastLogin(id) {
    try {
      await pool.query(
        `UPDATE users
         SET last_login = CURRENT_TIMESTAMP
         WHERE id = $1`,
        [id]
      );
    } catch (err) {
      console.error("User.updateLastLogin error:", err);
      throw err;
    }
  }
}

module.exports = User;
