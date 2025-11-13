// src/pages/Signup.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiEye, FiEyeOff, FiChevronLeft } from 'react-icons/fi';
import Congrat from '../../assets/img/congrats.png';

const API_BASE = import.meta?.env?.VITE_API_BASE || "https://genaiproject-production.up.railway.app/api";
const SIGNUP_PATH = "/auth/register";

const Signup = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  
  //기존 변수 이름 유지 (name, id)
  const [name, setName] = useState("");
  const [id, setId] = useState(""); // ← UI에서는 '아이디', 실제로는 email
  const [password, setPassword] = useState("");

  const [showPopup, setShowPopup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [serverResp, setServerResp] = useState(null);

  // 입력 검증
  const isFormValid =
    name.trim().length >= 1 &&
    id.trim().length >= 4 &&
    password.trim().length >= 6;

  const togglePassword = () => setShowPassword((v) => !v);

  //백엔드 연결 부분
  const handleSignup = async () => {
    if (!isFormValid || loading) return;
    setLoading(true);
    setErrorMsg("");
    setServerResp(null);

    try {
      // 실제 회원가입 API 호출
      const res = await fetch(`${API_BASE}${SIGNUP_PATH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: name.trim(),   // 백엔드 요구 스펙
          email: id.trim(),        // UI에서는 id, 백엔드에서는 email
          password: password.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.message || "회원가입 실패");
      }

      // 서버 응답 저장
      setServerResp({
        username: data.user.username,
        email: data.user.email,
      });

      setShowPopup(true); // 팝업 열기

    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || "회원가입 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && isFormValid && !loading) handleSignup();
  };

  const handleGoToLogin = () => navigate("/login");

  return (
    <div className="Signup_wrap container" onKeyDown={onKeyDown}>
      <div className="topbar topbar--simple">
        <button type="button" className="icon-btn" onClick={() => navigate(-1)}>
          <FiChevronLeft />
        </button>
      </div>

      <div className="title">
        <h2>안녕하세요 <span>👋</span></h2>
        <p>기본적인 정보를 등록해주세요</p>
      </div>

      {/* 이름 */}
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

      {/* 아이디 → 실제 서버에서는 email */}
      <div className="input-group">
        <label htmlFor="id">아이디 (이메일)</label>
        <input
          id="id"
          type="text"
          placeholder="example@test.com"
          value={id}
          onChange={(e) => setId(e.target.value)}
          required
        />
      </div>

      {/* 비밀번호 */}
      <div className="input-group">
        <label htmlFor="password">비밀번호</label>
        <div className="password-wrapper">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            placeholder="비밀번호를 입력해주세요 (6자 이상)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={6}
            required
          />
          <button type="button" className="toggle-btn" onClick={togglePassword}>
            {showPassword ? <FiEyeOff /> : <FiEye />}
          </button>
        </div>
      </div>

      {errorMsg && <div className="error-box">{errorMsg}</div>}

      <button
        className={`signup-btn ${isFormValid ? "active" : "inactive"}`}
        onClick={handleSignup}
        disabled={!isFormValid || loading}
      >
        {loading ? "가입 중…" : "회원가입"}
      </button>

      {/* 가입 완료 팝업 */}
      {showPopup && (
        <div className="popup-overlay">
          <div className="popup">
            <img
              src={Congrat}
              alt="회원가입 축하"
              style={{
                width: "100px",
                height: "100px",
                objectFit: "contain",
                display: "block",
                margin: "0 auto 20px",
              }}
            />

            <p>AI BEAUTY STYLIST (VIZY)</p>
            <p>서비스 가입을 축하드립니다 🎉</p>

            {serverResp && (
              <p style={{ opacity: 0.8, fontSize: 12 }}>
                이메일: <b>{serverResp.email}</b>
              </p>
            )}

            <p>아래 버튼을 눌러 이용을 시작하세요</p>

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
