import React, { useState, useRef, useLayoutEffect, useEffect } from "react";
import { useLocation } from "react-router-dom";
import "../assets/sass/mainface/faceresult.scss";
import { FiChevronLeft } from "react-icons/fi";

import yujinImg from "../assets/img/mainface/yujin.png";
import romandImg from "../assets/img/mainface/romand.png";
const TABS = [
  { key: "LIPS", label: "LIPS", icon: "💄" },
  { key: "CHEEKS", label: "CHEEKS", icon: "🌸" },
  { key: "EYES", label: "EYES", icon: "👁️" },
];

const FaceResult = () => {
  const { state } = useLocation();
  const imageUrl = state?.imageUrl;

  const [active, setActive] = useState("LIPS");
  const [isSheetOpen, setIsSheetOpen] = useState(false);

  const toggleSheet = () => {
    setIsSheetOpen((prev) => !prev);
  };

  // body 스크롤 방지
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

  return (
    <div className="container FaceResult_wrap">
      {/* 상단바 */}
      <header className="fr-topbar">
        <button className="fr-back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
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
              onClick={() => setActive(t.key)}
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
        <div className="prod-name">
          {active === "LIPS" && "Rom&nd Juicy Tint #Figfig"}
          {active === "CHEEKS" && "3CE Face Blush #Mono Pink"}
          {active === "EYES" && "Dasique Shadow Palette #Rose"}
        </div>
      </section>

      {/* BottomSheet */}
      <div className={`bsheet ${isSheetOpen ? "open" : ""}`}>
        <div className="bs-handle-area" onClick={toggleSheet}>
          <div className="bs-handle" />
        </div>

        <div className="bs-content">
          <div className="bs-card">
            <div className="bs-prod-img">
              <img src={romandImg} alt="Romand" />
            </div>

            <div className="bs-info">
              <h3>Rom&nd Juicy Tint #Figfig</h3>
              <ul className="spec">
                <li>ΔE 3.2</li>
                <li>Finish: Glossy</li>
                <li>유사도: 92%</li>
              </ul>
              <p className="desc">
                “이미지 속 립 컬러는 장밋빛 MLBB 계열로, Rom&nd Juicy Lasting
                Tint #Figfig와 색상 거리(ΔE 3.4)가 작습니다.”
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FaceResult;