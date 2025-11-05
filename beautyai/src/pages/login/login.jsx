import React, { useState } from 'react';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import Logo from '../../assets/img/main/Logo.png';

const API_BASE = import.meta?.env?.VITE_API_BASE || '';
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
          user_id: id.trim(),
          password: password.trim(),
        }),
      });

      if (!res.ok) {
        let msg = `로그인 실패 (HTTP ${res.status})`;
        try {
          const errJson = await res.clone().json();
          if (errJson?.message) msg = errJson.message;
        } catch {
          const text = await res.text().catch(() => '');
          if (text) msg = text;
        }
        if (res.status === 401 || /invalid/i.test(msg)) {
          msg = '아이디 또는 비밀번호가 올바르지 않습니다.';
        }
        throw new Error(msg);
      }

      const data = await res.json();
      if (!data?.access_token || !data?.user) {
        throw new Error('서버 응답 형식이 올바르지 않습니다.');
      }

      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/', { replace: true });
    } catch (err) {
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
    <label htmlFor="id">아이디</label>
    <input
      id="id"
      type="text"
      placeholder="아이디 입력"
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
  >
    로그인
  </button>

  <div className="signup-link">
    계정이 없으신가요? <br /><br /><a href="/signup">회원가입하기</a>
  </div>
</div>
  );
};

export default Login;
