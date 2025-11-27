// FaceResult.jsx
import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../assets/sass/mainface/faceresult.scss";
import { FiChevronLeft, FiHome } from "react-icons/fi";

import romandImg from "../assets/img/mainface/romand.png"; // FIXED


// 🔥 백엔드 응답 → UI 구조로 변환
const convertApiResult = (api) => {
  if (!api) return { LIPS: [], CHEEKS: [], EYES: [] };

  const convertList = (list) =>
    (list || []).map((p, idx) => ({
      tag: ["A", "B", "C"][idx],
      image: p.image_url,
      brand: p.brand,
      name: p.product_name,
      shade: p.shade_name,
      finish: p.finish,
      price: p.price,
      reason: p.reason,
    }));

  return {
    LIPS: convertList(api.lips?.recommendations),
    CHEEKS: convertList(api.cheeks?.recommendations),
    EYES: convertList(api.eyeshadow?.recommendations),
  };
};

const TABS = [
  { key: "LIPS", label: "LIPS", icon: "💄" },
  { key: "CHEEKS", label: "CHEEKS", icon: "🌸" },
  { key: "EYES", label: "EYES", icon: "👁️" },
];

const FaceResult = () => {
  const { state } = useLocation();
  const navigate = useNavigate();

  const imageUrl = state?.imageUrl;
  const pythonResults = convertApiResult(state?.results); // 🔥 변환 완료

  const [active, setActive] = useState("LIPS");
  const [isSheetOpen, setIsSheetOpen] = useState(false);

  const currentMatches = pythonResults[active] || [];

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

const handleTabClick = (tab) => {
  setActive(tab);
  setIsSheetOpen(false);
};
  return (
    <div className="container2 FaceResult_wrap">
      {/* 상단바 */}
      <header className="fr-topbar">
        <button className="fr-back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
        </button>
        <button className="fr-home-btn" onClick={() => navigate("/home")}>
          <FiHome />
        </button>
      </header>

      <h2 className="fr-title">분석 결과</h2>

      {/* 얼굴 이미지 */}
      <section className="fr-card">
        <div className="fr-photo">
          {imageUrl ? (
            <img src={imageUrl} alt="사용자 업로드 이미지" />
          ) : (
            <div>이미지가 없습니다</div>
          )}
        </div>

        {/* 탭 버튼 */}
        <div className="fr-segment">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`seg-btn ${active === t.key ? "active" : ""}`}
              onClick={() => handleTabClick(t.key)}
            >
              <span className="seg-ic">{t.icon}</span>
              <span className="seg-txt">{t.label}</span>
            </button>
          ))}
        </div>

        <p className="fr-hint">
          “각 부위를 클릭하면 해당 제품 분석 결과를 볼 수 있습니다.”
        </p>
      </section>

      {/* 제품 미리보기 */}
      <section className="fr-product">
        <div className="prod-img">
          <img src={romandImg} alt="product" />
        </div>
        <div className="prod-name">Top 3 추천 제품</div>
      </section>

      {/* BottomSheet */}
<div className={`bsheet ${isSheetOpen ? "open" : ""}`}>
  <div className="fr-handle-area" onClick={() => setIsSheetOpen(!isSheetOpen)}>
    <div className="fr-handle" />
  </div>

  <div className="fr-content">
    <div className="fr-compare-card">
      <div className="fr-compare-grid">

        {currentMatches.map((m, i) => (
          <div key={i} className="fr-compare-col">
            
            <div className="fr-col-title">MATCH {m.tag}</div>

            <div className="fr-col-thumb">
              <img src={m.image} alt="추천제품" />
            </div>

            {/* 브랜드 + 제품명 + 쉐이드 */}
            <div className="fr-col-name">
              <span className="fr-brand">{m.brand}</span>
              <span className="fr-product">{m.name}</span>
              {m.shade && <span className="fr-shade">{m.shade}</span>}
            </div>

            {/* 피니시 + 유사도 + 가격 */}
            <div className="fr-col-meta">
              <span className="fr-finish">{m.finish}</span>
              

              {m.price && (
                <span className="fr-price">{m.price.toLocaleString()}원</span>
              )}
            </div>

            {/* 추천 이유 */}
            <div className="fr-col-reason">{m.reason}</div>

          </div>
        ))}

      </div>

            <button className="fr-chat-btn" onClick={() => navigate("/chat")}>
              <span className="fr-chat-main">추천이 마음에 안 드나요?</span>
              <span className="fr-chat-sub">
                VIZY beauty stylist에게 물어보세요!
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FaceResult;
