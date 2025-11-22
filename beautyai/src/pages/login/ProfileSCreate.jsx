// src/pages/profile/ProfileCreate.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../../assets/sass/profile/profilesetting.scss";
import { FiChevronLeft } from "react-icons/fi";

const NODE_API = "https://genaiproject-production.up.railway.app/api";

export default function ProfileCreate() {
  const navigate = useNavigate();
  const [token, setToken] = useState("");

  // 토큰 확인
  useEffect(() => {
    const tk = localStorage.getItem("accessToken");
    if (!tk) {
      alert("로그인 후 사용해주세요.");
      navigate("/login");
      return;
    }
    setToken(tk);
  }, [navigate]);

  // 입력 필드
  const [personalColor, setPersonalColor] = useState("");
  const [skinUndertone, setSkinUndertone] = useState("");
  const [skinType, setSkinType] = useState("");
  const [contrastLevel, setContrastLevel] = useState("");
  const [preferredFinish, setPreferredFinish] = useState("");
  const [preferredStore, setPreferredStore] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");

  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!personalColor || !skinUndertone) {
      alert("퍼스널 컬러와 언더톤은 필수입니다.");
      return;
    }

    if (!token) {
      alert("로그인 정보가 없습니다. 다시 로그인 해주세요.");
      navigate("/login");
      return;
    }

    setLoading(true);

    const body = {
      personalColor,
      skinUndertone,
      skinType,
      contrastLevel,
      preferredFinish,
      preferredStore,
      priceRangeMin: priceMin ? parseInt(priceMin, 10) : undefined,
      priceRangeMax: priceMax ? parseInt(priceMax, 10) : undefined,
    };

    try {
      const res = await fetch(`${NODE_API}/profile/beauty`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (res.ok) {
        alert("프로필 생성 완료!");
        navigate("/home");
      } else {
        alert(data?.message || "프로필 생성에 실패했습니다.");
      }
    } catch (err) {
      console.error(err);
      alert("저장 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };
useEffect(() => {
  document.body.style.overflow = "hidden";
  return () => {
    document.body.style.overflow = "auto";
  };
}, []);

  return (
    <div className="ProfileSetting_wrap">
      {/* 탑바 */}
      <div className="ps-topbar">
        <button className="ps-back-btn" onClick={() => navigate(-1)}>
          <FiChevronLeft size={26} />
        </button>
        <h2>뷰티 프로필 생성</h2>
      </div>

      <div className="ps-content">
        {/* PERSONAL COLOR */}
        <div className="ps-block">
          <label>퍼스널 컬러 *</label>
          <select
            value={personalColor}
            onChange={(e) => setPersonalColor(e.target.value)}
          >
            <option value="">선택하세요</option>
            <option value="bright_spring">Bright Spring (브라이트 봄)</option>
            <option value="true_spring">True Spring (트루 봄)</option>
            <option value="light_spring">Light Spring (라이트 봄)</option>
            <option value="light_summer">Light Summer (라이트 여름)</option>
            <option value="true_summer">True Summer (트루 여름)</option>
            <option value="soft_summer">Soft Summer (소프트 여름)</option>
            <option value="soft_autumn">Soft Autumn (소프트 가을)</option>
            <option value="true_autumn">True Autumn (트루 가을)</option>
            <option value="deep_autumn">Deep Autumn (딥 가을)</option>
            <option value="deep_winter">Deep Winter (딥 겨울)</option>
            <option value="true_winter">True Winter (트루 겨울)</option>
            <option value="bright_winter">Bright Winter (브라이트 겨울)</option>
          </select>
        </div>

        {/* UNDERTONE */}
        <div className="ps-block">
          <label>피부 언더톤 *</label>
          <select
            value={skinUndertone}
            onChange={(e) => setSkinUndertone(e.target.value)}
          >
            <option value="">선택하세요</option>
            <option value="warm">Warm (웜톤)</option>
            <option value="cool">Cool (쿨톤)</option>
            <option value="neutral">Neutral (중성톤)</option>
          </select>
        </div>

        {/* 피부 타입 */}
        <div className="ps-block">
          <label>피부 타입</label>
          <select
            value={skinType}
            onChange={(e) => setSkinType(e.target.value)}
          >
            <option value="">선택 없음</option>
            <option value="oily">지성</option>
            <option value="dry">건성</option>
            <option value="combination">복합성</option>
            <option value="sensitive">민감성</option>
          </select>
        </div>

        {/* 명암 대비 */}
        <div className="ps-block">
          <label>명암 대비</label>
          <select
            value={contrastLevel}
            onChange={(e) => setContrastLevel(e.target.value)}
          >
            <option value="">선택 없음</option>
            <option value="high">높음</option>
            <option value="medium">중간</option>
            <option value="low">낮음</option>
          </select>
        </div>

        {/* 선호 피니시 */}
        <div className="ps-block">
          <label>선호 피니시</label>
          <select
            value={preferredFinish}
            onChange={(e) => setPreferredFinish(e.target.value)}
          >
            <option value="">선택 없음</option>
            <option value="matte">매트</option>
            <option value="glossy">글로시</option>
            <option value="satin">새틴</option>
            <option value="velvet">벨벳</option>
            <option value="dewy">촉촉</option>
          </select>
        </div>

        {/* 선호 매장 */}
        <div className="ps-block">
          <label>선호 매장</label>
          <select
            value={preferredStore}
            onChange={(e) => setPreferredStore(e.target.value)}
          >
            <option value="">선택 없음</option>
            <option value="roadshop">로드샵</option>
            <option value="department">백화점</option>
            <option value="online">온라인</option>
            <option value="luxury">럭셔리</option>
          </select>
        </div>

        {/* 가격대 */}
        <div className="ps-block">
          <label>가격대 (선택)</label>
          <div className="ps-price-row">
            <input
              type="number"
              placeholder="최소"
              value={priceMin}
              onChange={(e) => setPriceMin(e.target.value)}
            />
            <span>~</span>
            <input
              type="number"
              placeholder="최대"
              value={priceMax}
              onChange={(e) => setPriceMax(e.target.value)}
            />
          </div>
        </div>

        {/* 저장 버튼 */}
        <button
          className="ps-save-btn"
          onClick={handleCreate}
          disabled={loading}
        >
          {loading ? "저장 중..." : "프로필 생성하기"}
        </button>
      </div>
    </div>
  );
}
