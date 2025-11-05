// src/pages/Signup.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiEye, FiEyeOff, FiChevronLeft } from 'react-icons/fi';
import Congrat from '../../assets/img/congrats.png';

const API_BASE = import.meta?.env?.VITE_API_BASE || '';
const SIGNUP_PATH = '/auth/register'; // ← 명세대로

const Signup = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [name, setName] = useState('');
  const [id, setId] = useState('');           // → user_id로 전송
  const [password, setPassword] = useState('');
  const [showPopup, setShowPopup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [serverResp, setServerResp] = useState(null);

  // 최소 길이 검증 (명세)
  const isFormValid =
    name.trim().length >= 1 &&
    id.trim().length >= 4 &&
    password.trim().length >= 6;

  const togglePassword = () => setShowPassword(v => !v);

  const handleSignup = async () => {
  if (!isFormValid || loading) return;

  setLoading(true);
  setErrorMsg('');
  setServerResp(null);

  try {
    // ⚠️ [테스트용 목업 데이터 — 실제 API 호출 대신 실행]
    await new Promise((resolve) => setTimeout(resolve, 1000)); // 1초 대기 (로딩 연출)
    const mockData = {
      id: 1,
      name: name.trim(),
      user_id: id.trim(),
    };

    setServerResp(mockData);
    setShowPopup(true); // ✅ 팝업 강제 표시

    // 실제 API 호출 부분은 잠시 주석 처리 ↓
    /*
    const res = await fetch(`${API_BASE}${SIGNUP_PATH}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name.trim(),
        user_id: id.trim(),
        password: password.trim(),
      }),
    });

    if (res.status !== 201) {
      let message = '';
      try {
        const errJson = await res.clone().json();
        message = errJson?.message || '';
      } catch {
        message = await res.text().catch(() => '');
      }
      if (res.status === 409) throw new Error(message || '이미 사용 중인 아이디입니다.');
      if (res.status === 400) throw new Error(message || '입력값을 확인해 주세요.');
      throw new Error(message || `회원가입 실패 (HTTP ${res.status})`);
    }

    const data = await res.json();
    setServerResp(data);
    setShowPopup(true);
    */

  } catch (err) {
    console.error(err);
    setErrorMsg(err?.message || '회원가입 중 오류가 발생했습니다.');
  } finally {
    setLoading(false);
  }
};

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && isFormValid && !loading) handleSignup();
  };

  const handleGoToLogin = () => navigate('/login');

  return (
  <div className="Signup_wrap container" onKeyDown={onKeyDown}>
    {/* 기존 topbar 전체를 아래로 교체 */}
    <div className="topbar topbar--simple">
      <button
        type="button"
        className="icon-btn"
        aria-label="뒤로가기"
        onClick={() => navigate(-1)} // 항상 로그인으로 가려면 () => navigate('/login')
      >
        <FiChevronLeft />
      </button>
    </div>

    <div className="title">
      <h2>안녕하세요 <span>👋</span></h2>
      <p>기본적인 정보를 등록해주세요</p>
    </div>

      <div className="input-group">
        <label htmlFor="name">이름</label>
        <input
          id="name"
          type="text"
          placeholder="ex) 여성신"
          value={name}
          onChange={(e) => setName(e.target.value)}
          minLength={1}
          required
        />
      </div>

      <div className="input-group">
        <label htmlFor="id">아이디</label>
        <input
          id="id"
          type="text"
          placeholder="아이디를 입력해주세요 (4자 이상)"
          value={id}
          onChange={(e) => setId(e.target.value)}
          minLength={4}
          required
        />
        {id !== '' && id.trim().length < 4 && (
          <small className="hint error">아이디는 4자 이상이어야 합니다.</small>
        )}
      </div>

      <div className="input-group">
        <label htmlFor="password">비밀번호</label>
        <div className="password-wrapper">
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="비밀번호를 입력해주세요 (6자 이상)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={6}
            required
          />
          <button
            type="button"
            className="toggle-btn"
            onClick={togglePassword}
            aria-label={showPassword ? '비밀번호 숨기기' : '비밀번호 표시'}
          >
            {showPassword ? <FiEyeOff /> : <FiEye />}
          </button>
        </div>
        {password !== '' && password.trim().length < 6 && (
          <small className="hint error">비밀번호는 6자 이상이어야 합니다.</small>
        )}
      </div>

      {errorMsg && <div className="error-box">{errorMsg}</div>}

      <button
        className={`signup-btn ${isFormValid ? 'active' : 'inactive'}`}
        onClick={handleSignup}
        disabled={!isFormValid || loading}
        aria-disabled={!isFormValid || loading}
      >
        {loading ? '가입 중…' : '회원가입'}
      </button>

      {showPopup && (
  <div className="popup-overlay">
    <div className="popup">
      <div className="confetti">
        <img
          src={Congrat}
          alt="회원가입 축하"
          style={{
            width: '100px',
            height: '100px',
            objectFit: 'contain',
            display: 'block',
            margin: '0 auto 20px', // ✅ 중앙정렬 + 아래 여백
          }}
        />
      </div>

      <p>AI BEAUTY STYLIST (VIZY)</p>
      <p>서비스 가입을 축하드립니다</p>

      {serverResp && (
        <p style={{ opacity: 0.8, fontSize: 12 }}>
          가입 ID: <b>{serverResp.user_id}</b>
        </p>
      )}

      <p>아래 버튼을 눌러 서비스를 이용해주세요</p>

      <button className="popup-btn" onClick={handleGoToLogin}>
        로그인하기
      </button>
    </div>
  </div>
)}

    </div>
  );
};

export default Signup;