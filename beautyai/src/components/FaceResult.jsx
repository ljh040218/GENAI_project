import React, { useState, useRef, useLayoutEffect, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../assets/sass/mainface/faceresult.scss";

import { FiChevronLeft, FiHome } from "react-icons/fi";

import romandImg from "../assets/img/mainface/romand.png";
const TABS = [
  { key: "LIPS", label: "LIPS", icon: "💄" },
  { key: "CHEEKS", label: "CHEEKS", icon: "🌸" },
  { key: "EYES", label: "EYES", icon: "👁️" },
];

const MOCK_RESULTS = {
  LIPS: [
    {
      tag: "A",
      image: romandImg,
      brand: "Rom&nd",
      name: "#Figfig",
      finish: "Glossy",
      similarity: "99%",
      reason: "입술 색상과 가장 유사한 글로시 텍스처입니다.",
    },
    {
      tag: "B",
      image: romandImg,
      brand: "Rom&nd",
      name: "#Figfig",
      finish: "Glossy",
      similarity: "85%",
      reason: "톤이 비슷한 다른 글로시 립입니다.",
    },
    {
      tag: "C",
      image: romandImg,
      brand: "Rom&nd",
      name: "#Figfig",
      finish: "Matt",
      similarity: "80%",
      reason: "색상은 비슷하지만 매트 피니시입니다.",
    },
  ],
  CHEEKS: [],
  EYES: [],
};

const FaceResult = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const imageUrl = state?.imageUrl;
  const category = state?.category; // MainProduct에서 선택한 카테고리
  const results = state?.results || MOCK_RESULTS; // 카테고리별 top3 결과들
  // 현재 탭의 결과 리스트
  const [active, setActive] = useState(category); // 해당 카테고리만 활성화
  const [isSheetOpen, setIsSheetOpen] = useState(false);

  const currentMatches = results[active] || [];

  // 탭 버튼 변경 함수
  const handleTabClick = (tab) => {
    setActive(tab); // 미리보기 바뀜
    setIsSheetOpen(false); // 탭 바꾼 순간 bottom sheet 닫기 (UX good!)
  };
  const toggleSheet = () => {
    setIsSheetOpen((prev) => !prev);
  };
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

  // body 스크롤 방지
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

  return (
    <div className="container2 FaceResult_wrap ">
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

      {/* 얼굴 이미지 카드 */}
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
          <img
            src={
              active === "LIPS"
                ? romandImg
                : active === "CHEEKS"
                ? romandImg
                : active === "EYES"
                ? romandImg
                : romandImg
            }
            alt="product"
          />
        </div>
        <div className="prod-name">
          {active === "LIPS" && "Rom&nd Juicy Tint #Figfig"}
          {active === "CHEEKS" && "3CE Face Blush #Mono Pink"}
          {active === "EYES" && "Dasique Shadow Palette #Rose"}
        </div>
      </section>

      {/* BottomSheet */}
      <div className={`bsheet ${isSheetOpen ? "open" : ""}`}>
        <div className="fr-handle-area" onClick={toggleSheet}>
          <div className="fr-handle" />
        </div>

        <div className="fr-content">
          <div className="fr-compare-card">
            <div className="fr-compare-grid">
              {currentMatches.map((m, i) => (
                <div key={i} className="fr-compare-col">
                  <div className="fr-col-title">MATCH {m.tag}</div>
                  <div className="fr-col-thumb">
                    <img src={m.image} alt="" />
                  </div>
                  <div className="fr-col-name">
                    <span>{m.brand}</span>
                    <span>{m.name}</span>
                  </div>
                  <div className="fr-col-finish">{m.finish}</div>
                  <div className="fr-col-score">{m.similarity}</div>
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
