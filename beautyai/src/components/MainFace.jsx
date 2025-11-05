import React, { useState } from "react";
import "../assets/sass/mainface/mainface.scss";
import { FiChevronLeft } from "react-icons/fi";
import { FaUserCircle } from "react-icons/fa";

const MainFace = () => {
  const [showPopup, setShowPopup] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async () => {
    setShowPopup(true);
    setIsUploading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsUploading(false);
  };

  const handleCancel = () => {
    setShowPopup(false);
    setIsUploading(false);
  };

  return (
    <div className="MainFace_wrap container2">
      {/* 상단 뒤로가기 */}
      <header className="topbar">
        <button className="back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
        </button>
      </header>

      {/* 텍스트 + 아이콘 + 버튼을 하나로 */}
      <section className="upload-section">
        <h2 className="upload-title">
          원하는 인물의 사진을
          <br />
          업로드해주세요
        </h2>

        <div className="face-upload-icon">
          <FaUserCircle />
        </div>

        <button className="upload-btn" onClick={handleUpload}>
          사진 업로드하기
        </button>
      </section>

      {/* 주의사항 */}
      <div className="notice-box">
        <div className="notice-title">
          <span>⚠</span> 주의사항
        </div>
        <ul>
          <li>
            <strong>정면 사진</strong>을 업로드해주세요. 얼굴이 정면을 향하고,
            한쪽으로 치우치지 않은 사진이 가장 정확하게 분석됩니다.
          </li>
          <li>
            <strong>밝고 균일한 조명</strong>에서 촬영해주세요. 얼굴 일부가
            어둡거나 그림자가 지면 색상 분석이 왜곡될 수 있습니다.
          </li>
          <li>
            <strong>화장한 상태의 사진</strong>을 권장합니다. 립, 블러셔,
            아이메이크업의 실제 색상을 인식해 맞춤 제품을 추천합니다.
          </li>
          <li>
            <strong>배경은 단색 또는 깨끗한 벽면</strong>이 좋아요. 얼굴 인식
            (Face Parsing) 모델이 더 정확히 작동합니다.
          </li>
          <li>
            이미지는 <strong>JPG, PNG 형식</strong>으로 업로드할 수 있습니다.
          </li>
        </ul>
      </div>

      {/* 팝업 모달 */}
      {showPopup && (
        <div className="popup-overlay">
          <div className="popup">
            <div className="popup-icon">
              <FaUserCircle />
            </div>
            <h3>{isUploading ? "이미지 업로드 중..." : "업로드 완료"}</h3>
            <p>
              {isUploading
                ? "AI가 얼굴 부위를 인식 중입니다... 잠시만 기다려주세요."
                : "얼굴 인식이 완료되었습니다!"}
            </p>
            <button className="popup-btn" onClick={handleCancel}>
              {isUploading ? "업로드 취소" : "확인"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MainFace;
