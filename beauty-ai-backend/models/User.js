const pool = require("../config/database");

const User = {
  // 회원 생성
  async create(username, email, passwordHash) {
    try {
      const result = await pool.query(
        `INSERT INTO users (username, email, password_hash)
         VALUES ($1, $2, $3)
         RETURNING id, username, email, created_at`,
        [username, email, passwordHash]
      );
      return result.rows[0];
    } catch (error) {
      console.error("User.create error:", error);
      throw error;
    }
  },

  // 이메일로 조회
  async findByEmail(email) {
    const result = await pool.query(`SELECT * FROM users WHERE email = $1`, [email]);
    return result.rows[0];
  },

  // 유저네임으로 조회
  async findByUsername(username) {
    const result = await pool.query(`SELECT * FROM users WHERE username = $1`, [username]);
    return result.rows[0];
  },

  // ID로 조회
  async findById(id) {
    const result = await pool.query(
      `SELECT id, username, email, created_at, last_login FROM users WHERE id = $1`,
      [id]
    );
    return result.rows[0];
  },

  // 마지막 로그인 업데이트
  async updateLastLogin(id) {
    await pool.query(`UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1`, [id]);
  }
};

module.exports = User;