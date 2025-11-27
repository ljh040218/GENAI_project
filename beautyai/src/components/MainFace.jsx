// MainFace.jsx
import React, { useRef, useState,useEffect} from "react";
import { useNavigate } from "react-router-dom";
import "../assets/sass/mainface/mainface.scss";
import { FiChevronLeft } from "react-icons/fi";
import { FaUserCircle } from "react-icons/fa";


const PYTHON_API = "https://pythonapi-production-8efe.up.railway.app";

const MainFace = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [showPopup, setShowPopup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // 파일 선택창 열기
  const openFilePicker = () => fileInputRef.current.click();

  // 파일 선택 후
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 로컬에서 미리보기용 URL (FaceResult에서 보여줄 이미지)
    const imgURL = URL.createObjectURL(file);

    // 팝업 켜기 + 로딩 시작
    setShowPopup(true);
    setIsLoading(true);

     const formData = new FormData();
  formData.append("file", file);

  let apiResult = null;

  try {
      const response = await fetch(`${PYTHON_API}/api/analyze/image`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      });

  apiResult = await response.json();
      console.log("🔥 얼굴 분석 API 응답:", apiResult);

    } catch (error) {
      console.error("Face API Error:", error);
    }

    setIsLoading(false);

    // 네비게이트
    setTimeout(() => {
      navigate("/faceresult", {
        state: {
          imageUrl: imgURL,
          results: apiResult, // ⭐ FaceResult가 필요한 구조 그대로 전달
        },
      });
    }, 500);
  };

  // 스크롤 방지
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

  
  return (
    <div className="MainFace_wrap container2">
      {/* 상단바 */}
      <header className="topbar">
        <button className="back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
        </button>
      </header>

      {/* 업로드 섹션 */}
      <section className="upload-section">
        <h2 className="upload-title">
          원하는 인물의 사진을<br />업로드해주세요
        </h2>

        <div className="face-upload-icon">
          <FaUserCircle />
        </div>

        {/* 숨겨진 file input */}
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          style={{ display: "none" }} // 완전 숨김
          onChange={handleFileChange}
        />

        <button className="upload-btn" onClick={openFilePicker}>
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
      {/* 로딩 팝업 */}
      {showPopup && (
        <div className="popup-overlay">
          <div className="popup">
            <div className="popup-icon">
              <FaUserCircle />
            </div>

            <h3>{isLoading ? "이미지 분석 중..." : "완료!"}</h3>
            <p>
              {isLoading
                ? "AI가 얼굴을 분석하고 있습니다..."
                : "얼굴 인식이 완료되었습니다!"}
            </p>

            {!isLoading && (
              <button className="popup-btn" onClick={() => setShowPopup(false)}>
                확인
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MainFace;
