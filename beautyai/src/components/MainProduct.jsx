// MainProduct.jsx
import React, { useRef, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../assets/sass/mainproduct/mainproduct.scss";
import { FiChevronLeft } from "react-icons/fi";
import { FaCamera } from "react-icons/fa";

const PYTHON_API = "https://pythonapi-production-8efe.up.railway.app";

const MainProduct = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [imageURL, setImageURL] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const [showCategoryPopup, setShowCategoryPopup] = useState(false);
  const [showLoadingPopup, setShowLoadingPopup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const openFilePicker = () => fileInputRef.current.click();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const imgURL = URL.createObjectURL(file);
    setImageURL(imgURL);
    setSelectedFile(file);

    setShowCategoryPopup(true);
  };

  // 카테고리 선택 시 Python API 호출
  const selectCategory = async (categoryKey) => {
    if (!selectedFile) {
      alert("먼저 제품 이미지를 업로드해주세요.");
      return;
    }

    // API에서 사용하는 카테고리 문자열 (소문자)
    const apiCategory = categoryKey.toLowerCase(); // "LIPS" → "lips"

    setShowCategoryPopup(false);
    setShowLoadingPopup(true);
    setIsLoading(true);

    try {
      const token = localStorage.getItem("accessToken"); // 로그인 시 저장해둔 토큰 사용

      const formData = new FormData();
      formData.append("file", selectedFile);

      console.log("👉 보내는 카테고리:", apiCategory);
      console.log("👉 보내는 파일:", selectedFile);

      const response = await fetch(
        `${PYTHON_API}/api/product/recommend?category=${apiCategory}`,
        {
          method: "POST",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`추천 API 요청 실패: ${response.status}`);
      }

      const data = await response.json();
      console.log("👈 받은 추천 결과:", data);

      setIsLoading(false);

      // 살짝 딜레이 후 로딩 팝업 닫고 결과 페이지로 이동
      setTimeout(() => {
        setShowLoadingPopup(false);

        navigate("/productresult", {
          state: {
            imageUrl: imageURL,
            category: categoryKey,
            apiCategory,
            pythonResult: data,
          },
        });
      }, 500);
    } catch (error) {
      console.error(error);
      setIsLoading(false);
      setShowLoadingPopup(false);
      alert("제품 추천 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    }
  };
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

  return (
    <div className="MainProduct_wrap container2">
      <header className="topbar">
        <button className="back-btn" onClick={() => window.history.back()}>
          <FiChevronLeft />
        </button>
      </header>

      <section className="upload-section">
        <h2 className="upload-title">
          유사한 색상의 제품을
          <br />
          추천해드릴게요
        </h2>

        <div className="product-upload-icon">
          <FaCamera />
        </div>

        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={handleFileChange}
        />

        <button className="upload-btn" onClick={openFilePicker}>
          제품 사진 업로드하기
        </button>
      </section>

      <div className="notice-box">
        <div className="notice-title">
          <span>⚠</span> 주의사항
        </div>
        <ul>
          <li>
            정면 사진을 업로드해주세요. 얼굴이 정면을 향하고, 한쪽으로 치우치지
            않은 사진이 가장 정확하게 분석됩니다.
          </li>
          <li>
            제품이 기울어지거나 잘리지 않도록 정면에서 촬영해야 정확히 인식할 수
            있습니다.
          </li>
          <li>
            밝고 균일한 조명에서 촬영해주세요. 어두운 조명, 그림자, 형광등 빛은
            실제 색상과 다르게 인식될 수 있습니다.
          </li>
          <li>
            배경은 단색 또는 깨끗한 벽면이 좋아요. 복잡한 배경은 AI가 제품
            영역을 구분하기 어렵게 만듭니다.
          </li>
          <li>제품 라벨이 보이도록 촬영해주세요.</li>
          <li>JPG 또는 PNG 형식을 권장합니다.</li>
        </ul>
      </div>

      {showCategoryPopup && (
        <div className="popup-overlay">
          <div className="popup category-popup">
            <h3>이 제품은 어떤 종류인가요?</h3>
            <p>정확한 분석을 위해 선택해주세요.</p>

            <div className="category-buttons">
              <button onClick={() => selectCategory("LIPS")}>💄 립</button>
              <button onClick={() => selectCategory("CHEEKS")}>🌸 치크</button>
              <button onClick={() => selectCategory("EYES")}>
                👁 아이섀도우
              </button>
            </div>

            <button
              className="popup-close"
              onClick={() => setShowCategoryPopup(false)}
            >
              취소
            </button>
          </div>
        </div>
      )}

      {showLoadingPopup && (
  <div className="popup-overlay">
    <div className="popup loading-popup">

      <div className="popup-icon">
        <FaCamera />
      </div>

      {/* ✅ 로딩 중 */}
      {isLoading && (
        <>
          <h3 className="loading-title">이미지 분석 중</h3>
          <div className="loading-spinner"></div>
          <p className="loading-text">AI가 제품 이미지를 분석하고 있어요</p>
        </>
      )}

      {/* ✅ 완료 */}
      {!isLoading && (
        <>
          <h3>완료!</h3>
          <p>분석이 완료되었습니다!</p>
        </>
      )}

    </div>
  </div>
)}

    </div>
  );
};

export default MainProduct;
