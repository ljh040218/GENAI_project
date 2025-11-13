// src/pages/Login.jsx
import React, { useState } from 'react';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import Logo from '../../assets/img/main/Logo.png';

const API_BASE = import.meta?.env?.VITE_API_BASE || "https://genaiproject-production.up.railway.app/api";
const API_PATH = '/auth/login';

const Login = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const [id, setId] = useState('');
  const [password, setPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const togglePasswordVisibility = () => setShowPassword(v => !v);

  const isFormValid = id.trim().length >= 4 && password.trim().length >= 6;

  const handleLogin = async () => {
  if (!isFormValid || loading) return;

  setLoading(true);
  setErrorMsg('');

  try {
    const res = await fetch(`${API_BASE}${API_PATH}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: id.trim(),      // 서버 요구: email
        password: password.trim(),
      }),
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data?.message || '로그인 실패');
    }

    // JWT + 유저정보 저장
    localStorage.setItem('accessToken', data.accessToken);
    localStorage.setItem('refreshToken', data.refreshToken);
    localStorage.setItem('user', JSON.stringify(data.user));

    // 로그인 성공 시 Home으로 이동
    navigate('/home', { replace: true });

  } catch (err) {
    console.error(err);
    setErrorMsg(err?.message || '로그인 중 오류가 발생했습니다.');
  } finally {
    setLoading(false);
  }
};

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && isFormValid && !loading) handleLogin();
  };

  return (
    <div className="Login_wrap container" onKeyDown={onKeyDown}>
      <div className="logo-box">
        <img src={Logo} alt="VIZY Beauty Stylist" style={{ width: '270px', height: 'auto' }}/>
      </div>

      <div className="input-group">
        <label htmlFor="id">아이디 (이메일)</label>
        <input
          id="id"
          type="text"
          placeholder="example@test.com"
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
      </div>

      <div className="input-group">
        <label htmlFor="password">비밀번호</label>
        <div className="password-wrapper">
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="비밀번호 입력"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="button"
            className="toggle-btn"
            onClick={togglePasswordVisibility}
          >
            {showPassword ? <FiEyeOff /> : <FiEye />}
          </button>
        </div>
      </div>

      {errorMsg && <div className="error-box">{errorMsg}</div>}

      <button
        className={`login-btn ${isFormValid ? 'active' : 'inactive'}`}
        onClick={handleLogin}
        disabled={!isFormValid || loading}
      >
        {loading ? "로그인 중…" : "로그인"}
      </button>

      <div className="signup-link">
        계정이 없으신가요? <br /><br />
        <a href="/signup">회원가입하기</a>
      </div>
    </div>
  );
};

export default Login;
