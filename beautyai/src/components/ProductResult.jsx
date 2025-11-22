// ProductResult.jsx
import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../assets/sass/mainproduct/productresult.scss";
import { FiChevronLeft, FiHome } from "react-icons/fi";

const TABS = [
  { key: "LIPS", name: "LIPS", icon: "💄" },
  { key: "CHEEKS", name: "CHEEKS", icon: "🌸" },
  { key: "EYES", name: "EYES", icon: "👁️" },
];

const NAME_BY_TAB = {
  LIPS: "Rom&nd Juicy Tint #Figfig",
  CHEEKS: "3CE Face Blush #Mono Pink",
  EYES: "Dasique Shadow Palette #Rose",
};

const ProductResult = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const imageUrl = state?.imageUrl;
  const category = state?.category; // MainProduct에서 선택한 카테고리
  const results = state?.results || {}; // 카테고리별 top3 결과들

  const [active, setActive] = useState(category); // 해당 카테고리만 활성화
  const [sheetOpen, setSheetOpen] = useState(false);

  const currentMatches = results[active] || []; // 현재 카테고리의 top3

  const toggleSheet = () => setSheetOpen((prev) => !prev);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

  return (
    <div className="ProductResult_wrap container2">
      <header className="pr-topbar">
        <button className="pr-back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
        </button>
        <button className="pr-home-btn" onClick={() => navigate("/home")}>
          <FiHome />
        </button>
      </header>

      <h2 className="pr-title">분석 결과</h2>

      <section className="pr-card">
        <div className="pr-photo">
          {imageUrl ? <img src={imageUrl} alt="uploaded" /> : "이미지 없음"}
        </div>

        {/* 선택된 카테고리 외에는 클릭 불가 */}
        <div className="pr-segment">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`pr-seg-btn ${
                active === tab.key ? "active" : "disabled"
              }`}
              disabled={active !== tab.key}
              onClick={() => {
                if (active === tab.key) setActive(tab.key);
              }}
            >
              {tab.icon} {tab.name}
            </button>
          ))}
        </div>

        <div className="pr-prod-name">{NAME_BY_TAB[active]}</div>
        <p className="pr-hint">* AI 분석 결과와 유사한 상위 3개 제품입니다.</p>
      </section>

      {/* 하단 BottomSheet */}
      <div className={`pr-bsheet ${sheetOpen ? "open" : ""}`}>
        <div className="pr-bs-handle-area" onClick={toggleSheet}>
          <div className="pr-bs-handle" />
        </div>

        <div className="pr-bs-content">
          <div className="pr-compare-card">
            <div className="pr-compare-grid">
              {currentMatches.map((m, i) => (
                <div key={i} className="pr-compare-col">
                  <div className="pr-col-title">MATCH {m.tag}</div>
                  <div className="pr-col-thumb">
                    <img src={m.image} alt="" />
                  </div>
                  <div className="pr-col-name">
                    <span>{m.brand}</span>
                    <span>{m.name}</span>
                  </div>
                  <div className="pr-col-finish">{m.finish}</div>
                  <div className="pr-col-score">{m.similarity}</div>
                  <div className="pr-col-reason">{m.reason}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductResult;
