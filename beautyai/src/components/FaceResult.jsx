import React, { useState, useRef, useLayoutEffect } from "react";
import { useLocation } from "react-router-dom";
import "../assets/sass/mainface/faceresult.scss";
import { FiChevronLeft } from "react-icons/fi";
import yujinImg from "../assets/img/faceresult/yujin.png";
import romandImg from "../assets/img/faceresult/romand.png";

const TABS = [
  { key: "LIPS", label: "LIPS", icon: "💄" },
  { key: "CHEEKS", label: "CHEEKS", icon: "🌸" },
  { key: "EYES", label: "EYES", icon: "👁️" },
];

const FaceResult = () => {
  const { state } = useLocation();
  const imageUrl = state?.imageUrl; // MainFace에서 navigate로 넘긴 URL
  const [active, setActive] = useState("LIPS");

  const sheetRef = useRef(null);
  const [sheetY, setSheetY] = useState(0); //현재 Y 이동
  const posRef = useRef({ start: 0, y: 0 }); // 내부 상태
  const HANDLE = 72; // 핸들이 보일 높이
  const SHEET_RATIO = 0.75; // 75vh

  const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

  // 초기: 핸들만 보이도록 접힘 위치로
  useLayoutEffect(() => {
    const setCollapsed = () => {
      const vh = window.innerHeight;
      const h = vh * SHEET_RATIO; // 시트 실제 px 높이
      const collapsedPx = Math.max(0, h - HANDLE);
      posRef.current.y = collapsedPx;
      setSheetY(collapsedPx);
    };
    setCollapsed();
    window.addEventListener("resize", setCollapsed);
    return () => window.removeEventListener("resize", setCollapsed);
  }, []);

  const onMove = (e) => {
    const vh = window.innerHeight;
    const h = vh * SHEET_RATIO;
    const collapsedPx = Math.max(0, h - HANDLE);
    let next = e.clientY - posRef.current.start; // 양수: 아래
    // 바닥에 붙인 상태: 열림은 0, 닫힘은 collapsedPx
    next = clamp(next, 0, collapsedPx);
    posRef.current.y = next;
    setSheetY(next);
  };

  const endDrag = () => {
    const vh = window.innerHeight;
    const h = vh * SHEET_RATIO;
    const collapsedPx = Math.max(0, h - HANDLE);
    const mid = collapsedPx / 2;
    const y = posRef.current.y;

    // 두 상태만: 0(열림) / collapsedPx(닫힘)
    const target = y <= mid ? 0 : collapsedPx;

    posRef.current.y = target;
    setSheetY(target);

    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", endDrag);
  };

  const startDrag = (clientY) => {
    posRef.current.start = clientY - posRef.current.y;
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", endDrag);
  };

  return (
    <div className="FaceResult_wrap container2">
      {/* 상단 뒤로가기 */}
      <header className="fr-topbar">
        <button className="fr-back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
        </button>
      </header>

      <h2 className="fr-title">분석 결과</h2>

      {/* 업로드 이미지 카드 */}
      <section className="fr-card">
        <div className="fr-photo">
          {/* {imageUrl ? (
            <img src={imageUrl} alt="uploaded" />
          ) : (
            <div className="fr-photo-placeholder">업로드한 이미지</div>
          )} */}
          <img src={yujinImg} alt="유진" />
        </div>

        {/* 세그먼트 버튼 */}
        <div className="fr-segment">
          {TABS.map(({ key, label, icon }) => (
            <button
              key={key}
              className={`seg-btn ${active === key ? "active" : ""}`}
              onClick={() => setActive(key)}
            >
              <span className="seg-ic">{icon}</span>
              <span className="seg-txt">{label}</span>
            </button>
          ))}
        </div>

        <p className="fr-hint">
          “각 부위를 클릭하면 해당 제품 분석 결과를 볼 수 있습니다.”
        </p>
      </section>

      {/* 제품 영역 (UI만) */}
      <section className="fr-product">
        <div className={`prod-img ${active.toLowerCase()}`}>
          {active === "LIPS" && <img src={romandImg} alt="Rom&nd" />}
          {active === "CHEEKS" && <img src={romandImg} alt="Rom&nd" />}
          {active === "EYES" && <img src={romandImg} alt="Rom&nd" />}
        </div>
        <div className="prod-name">
          {active === "LIPS" && "Rom&nd Juicy Tint #Figfig"}
          {active === "CHEEKS" && "3CE Face Blush #Mono Pink"}
          {active === "EYES" && "Dasique Shadow Palette #Rose"}
        </div>
      </section>

      {/* 하단 핑크 바 */}
      <div
        ref={sheetRef}
        className="bsheet container2"
        style={{ transform: `translateY(${sheetY}px)` }}
      >
        <div
          className="bs-handle-area"
          onPointerDown={(e) => startDrag(e.clientY)}
        >
          <div className="bs-handle" />
        </div>

        <div className="bs-content">
          {/* 스크롤 올린 페이지*/}
          <div className="bs-card">
            <div className="bs-prod-img">
              <img src={romandImg} alt="Rom&nd" />
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
