// src/pages/profile/ProfileEdit.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../assets/sass/profile/profilesetting.scss";
import { FiChevronLeft } from "react-icons/fi";

const NODE_API = "https://genaiproject-production.up.railway.app/api";

export default function ProfileEdit() {
  const navigate = useNavigate();
  const [token, setToken] = useState("");

  // 프로필 데이터 상태값들
  const [personalColor, setPersonalColor] = useState("");
  const [skinUndertone, setSkinUndertone] = useState("");
  const [skinType, setSkinType] = useState("");
  const [contrastLevel, setContrastLevel] = useState("");
  const [preferredFinish, setPreferredFinish] = useState("");
  const [preferredStore, setPreferredStore] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");

  const [loading, setLoading] = useState(false);

  // 🔥 페이지 로드 시 토큰 확인 + 기존 프로필 자동 로드
  useEffect(() => {
    const tk = localStorage.getItem("accessToken");
    if (!tk) {
      alert("로그인 후 이용해주세요.");
      navigate("/login");
      return;
    }

    setToken(tk);
    fetchProfile(tk);

  document.body.style.overflow = "hidden";
  return () => {
    document.body.style.overflow = "auto";
  };
}, []);


  // 🔥 GET - 프로필 조회
  const fetchProfile = async (tk) => {
    try {
      const res = await fetch(`${NODE_API}/profile/beauty`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${tk}`,
        },
      });

      const data = await res.json();

      if (!res.ok || !data.profile) {
        alert("프로필이 존재하지 않습니다.");
        return;
      }

      // 데이터를 state로 채움 (응답은 data.profile 임)
      const p = data.profile;

      setPersonalColor(p.personalColor || "");
      setSkinUndertone(p.skinUndertone || "");
      setSkinType(p.skinType || "");
      setContrastLevel(p.contrastLevel || "");
      setPreferredFinish(p.preferredFinish || "");
      setPreferredStore(p.preferredStore || "");
      setPriceMin(p.priceRangeMin || "");
      setPriceMax(p.priceRangeMax || "");
    } catch (err) {
      console.error("조회 실패:", err);
      alert("프로필을 불러오는 중 오류가 발생했습니다.");
    }
  };

  // 🔥 PUT - 프로필 수정 요청
  const handleUpdate = async () => {
    if (!personalColor || !skinUndertone) {
      alert("퍼스널 컬러와 언더톤은 필수입니다.");
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
      priceRangeMin: priceMin ? Number(priceMin) : null,
      priceRangeMax: priceMax ? Number(priceMax) : null,
    };

    try {
      const res = await fetch(`${NODE_API}/profile/beauty`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (res.ok) {
        alert("프로필 수정 완료!");
        navigate("/profileview");
      } else {
        alert(data.message || "수정 실패");
      }
    } catch (err) {
      console.error(err);
      alert("오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ProfileSetting_wrap">
      {/* 탑바 */}
      <div className="ps-topbar">
        <button className="ps-back-btn" onClick={() => navigate(-1)}>
          <FiChevronLeft size={26} />
        </button>
        <h2>프로필 수정</h2>
      </div>

      {/* 본문 */}
      <div className="ps-content">
        {/* 개인 정보 선택들 */}

        <div className="ps-block">
          <label>퍼스널 컬러 *</label>
          <select value={personalColor} onChange={(e) => setPersonalColor(e.target.value)}>
            <option value="">선택하세요</option>
            <option value="bright_spring">Bright Spring</option>
            <option value="true_spring">True Spring</option>
            <option value="light_spring">Light Spring</option>
            <option value="light_summer">Light Summer</option>
            <option value="true_summer">True Summer</option>
            <option value="soft_summer">Soft Summer</option>
            <option value="soft_autumn">Soft Autumn</option>
            <option value="true_autumn">True Autumn</option>
            <option value="deep_autumn">Deep Autumn</option>
            <option value="deep_winter">Deep Winter</option>
            <option value="true_winter">True Winter</option>
            <option value="bright_winter">Bright Winter</option>
          </select>
        </div>

        <div className="ps-block">
          <label>피부 언더톤 *</label>
          <select value={skinUndertone} onChange={(e) => setSkinUndertone(e.target.value)}>
            <option value="">선택하세요</option>
            <option value="warm">Warm (웜톤)</option>
            <option value="cool">Cool (쿨톤)</option>
            <option value="neutral">Neutral (중성톤)</option>
          </select>
        </div>

        <div className="ps-block">
          <label>피부 타입</label>
          <select value={skinType} onChange={(e) => setSkinType(e.target.value)}>
            <option value="">선택 없음</option>
            <option value="oily">지성</option>
            <option value="dry">건성</option>
            <option value="combination">복합성</option>
            <option value="sensitive">민감성</option>
          </select>
        </div>

        <div className="ps-block">
          <label>명암 대비</label>
          <select value={contrastLevel} onChange={(e) => setContrastLevel(e.target.value)}>
            <option value="">선택 없음</option>
            <option value="high">높음</option>
            <option value="medium">중간</option>
            <option value="low">낮음</option>
          </select>
        </div>

        <div className="ps-block">
          <label>선호 피니시</label>
          <select value={preferredFinish} onChange={(e) => setPreferredFinish(e.target.value)}>
            <option value="">선택 없음</option>
            <option value="matte">매트</option>
            <option value="glossy">글로시</option>
            <option value="satin">새틴</option>
            <option value="velvet">벨벳</option>
            <option value="dewy">촉촉</option>
          </select>
        </div>

        <div className="ps-block">
          <label>선호 매장</label>
          <select value={preferredStore} onChange={(e) => setPreferredStore(e.target.value)}>
            <option value="">선택 없음</option>
            <option value="roadshop">로드샵</option>
            <option value="department">백화점</option>
            <option value="online">온라인</option>
            <option value="luxury">럭셔리</option>
          </select>
        </div>

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
        <button className="ps-save-btn" onClick={handleUpdate} disabled={loading}>
          {loading ? "저장 중…" : "수정하기"}
        </button>
      </div>
    </div>
  );
}
