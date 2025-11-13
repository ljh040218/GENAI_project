import React, { useState, useRef, useLayoutEffect } from "react";
import { useLocation } from "react-router-dom";
import "../assets/sass/mainproduct/productresult.scss";
import { FiChevronLeft } from "react-icons/fi";
import romandImg from "../assets/img/faceresult/romand.png";

const TABS = [
  { key: "LIPS", label: "LIPS", icon: "💄" },
  { key: "CHEEKS", label: "CHEEKS", icon: "🌸" },
  { key: "EYES", label: "EYES", icon: "👁️" },
];

// DB 연동 전, 탭별 더미 제품명
const NAME_BY_TAB = {
  LIPS: "Rom&nd Juicy Tint #Figfig",
  CHEEKS: "3CE Face Blush #Mono Pink",
  EYES: "Dasique Shadow Palette #Rose",
};

const MOCK_MATCHES = [
  {
    tag: "A",
    image: romandImg,
    brand: "Rom&nd",
    name: "#Figfig",
    finish: "Glossy",
    similarity: "99%",
    reason: "추천이유추천이유추천이유",
  },
  {
    tag: "B",
    image: romandImg,
    brand: "Rom&nd",
    name: "#Figfig",
    finish: "Glossy",
    similarity: "85%",
    reason: "추천이유추천이유추천이유",
  },
  {
    tag: "C",
    image: romandImg,
    brand: "Rom&nd",
    name: "#Figfig",
    finish: "Matt",
    similarity: "80%",
    reason: "추천이유추천이유추천이유",
  },
];

const FaceResult = () => {
  const { state } = useLocation();
  const imageUrl = state?.imageUrl; // MainFace에서 navigate로 넘긴 URL
  const [active, setActive] = useState("LIPS");
  // 나중에 DB에서 넘겨줄 수 있는 형태: state?.names = { LIPS: "...", CHEEKS: "...", EYES: "..." }
  const productName =
    (state?.names && state.names[active]) ||
    NAME_BY_TAB[active] ||
    "제품명 로딩 중…";

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
    <div className="ProductResult_wrap container2">
      {/* 상단 뒤로가기 */}
      <header className="pr-topbar">
        <button className="pr-back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
        </button>
      </header>

      <h2 className="pr-title">분석 결과</h2>

      {/* 업로드 이미지 카드 */}
      <section className="pr-card">
        <div className="pr-photo">
          {/* {imageUrl ? (
            <img src={imageUrl} alt="uploaded" />
          ) : (
            <div className="fr-photo-placeholder">업로드한 이미지</div>
          )} */}
          <img src={romandImg} alt="롬앤" />
        </div>

        {/* 세그먼트 버튼 */}
        <div className="pr-segment">
          {TABS.map(({ key, label, icon }) => (
            <button
              key={key}
              className={`pr-seg-btn ${active === key ? "active" : ""}`}
              onClick={() => setActive(key)}
            >
              <span className="pr-seg-ic">{icon}</span>
              <span className="pr-seg-txt">{label}</span>
            </button>
          ))}
        </div>
        {/* 제품명 (지금은 더미, 나중에 DB 값으로 대체) */}
        <div className="pr-prod-name">{productName}</div>

        <p className="pr-hint">
          * 버튼를 클릭하면 해당 제품 분석 결과를 볼 수 있습니다.
        </p>
      </section>

      {/* 하단 핑크 바 */}
      <div
        ref={sheetRef}
        className="pr-bsheet container2"
        style={{ transform: `translateY(${sheetY}px)` }}
      >
        <div
          className="pr-bs-handle-area"
          onPointerDown={(e) => startDrag(e.clientY)}
        >
          <div className="pr-bs-handle" />
        </div>

        <div className="pr-bs-content">
          {/* 비교 그리드 카드 (목데이터 렌더링) */}
          <div className="pr-compare-card">
            <div className="pr-compare-grid">
              {MOCK_MATCHES.map((m, i) => (
                <div key={m.tag} className="pr-compare-col" data-index={i}>
                  {/* 헤더: MATCH A/B/C */}
                  <div className="pr-col-title">
                    MATCH
                    <br />
                    {m.tag}
                  </div>

                  {/* 썸네일 */}
                  <div className="pr-col-thumb">
                    <img
                      src={m.image}
                      alt={`${m.brand || ""} ${m.name || ""}`}
                    />
                  </div>

                  {/* 제품명 (2줄) : brand/name 없으면 name을 \n 분리해서 표시 */}
                  <div className="pr-col-name">
                    {m.brand || m.name ? (
                      <>
                        {m.brand && <span>{m.brand}</span>}
                        {m.name && <span>{m.name}</span>}
                      </>
                    ) : (
                      (m.title || "")
                        .split(/\n/)
                        .map((t, idx) => <span key={idx}>{t}</span>)
                    )}
                  </div>

                  {/* 피니시 */}
                  <div className="pr-col-finish">{m.finish}</div>

                  {/* 유사도 */}
                  <div className="pr-col-score">{m.similarity}</div>

                  {/* 추천 이유 */}
                  <div className="pr-col-reason">
                    {(m.reason || "").split("\n").map((line, idx) => (
                      <p key={idx}>{line}</p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FaceResult;
