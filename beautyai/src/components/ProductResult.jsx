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

const ProductResult = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const imageUrl = state?.imageUrl;
  const category = state?.category; // MainProduct에서 선택한 카테고리
  // Python 백엔드 응답
  const pythonResult = state?.pythonResult;
  const resultList = pythonResult?.results || [];

  const [active, setActive] = useState(category); // 해당 카테고리만 활성화
  const [sheetOpen, setSheetOpen] = useState(false);

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

        <div className="pr-prod-name">
          {resultList[0]?.brand} {resultList[0]?.product_name}
        </div>
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
              {resultList.map((item, i) => (
                <div key={i} className="pr-compare-col">
                  <div className="pr-col-title">
                    MATCH {i === 0 ? "A" : i === 1 ? "B" : "C"}
                  </div>
                  <div className="pr-col-thumb">
                    <img src={item.image_url} alt="" />
                  </div>
                  <div className="pr-col-name">
                    <span className="pr-brand">{item.brand}</span>
                    <span className="pr-product">{item.product_name}</span>
                    {item.shade_name && (
                      <span className="pr-shade">{item.shade_name}</span>
                    )}
                  </div>
                  {/* 피니시 + 유사도 */}
                  <div className="pr-col-meta">
                    <span className="pr-finish">{item.finish}</span>
                    {item.price && (
                      <span className="pr-price">
                        {item.price.toLocaleString()}원
                      </span>
                    )}
                  </div>
                  <div className="pr-col-reason">{item.reason}</div>
                </div>
              ))}
            </div>
            <button className="pr-chat-btn" onClick={() => navigate("/chat")}>
              <span className="pr-chat-main">추천이 마음에 안 드나요?</span>
              <span className="pr-chat-sub">
                VIZY beauty stylist에게 물어보세요!
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductResult;
