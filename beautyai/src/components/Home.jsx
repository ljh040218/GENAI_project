// src/pages/Home.jsx
import React, { useEffect, useState } from "react"; 
import "../assets/sass/home/home.scss";
import { FiUser } from "react-icons/fi";   // 🔥 메뉴 대신 유저 아이콘만 사용
import { Swiper, SwiperSlide } from "swiper/react";
import { Pagination, Autoplay } from "swiper/modules";
import "swiper/css";
import "swiper/css/pagination";
import { useNavigate } from "react-router-dom";

import Card1 from "../../src/assets/img/card1.svg"
import Card2 from "../../src/assets/img/card2.svg";
import Card3 from "../../src/assets/img/card3.svg";

const API_BASE = "https://genaiproject-production.up.railway.app/api";

const Home = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [showProfilePopup, setShowProfilePopup] = useState(false);

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setUsername(user.username);
      } catch (e) {
        console.error("유저 파싱 실패:", e);
      }
    }
     document.body.style.overflow = "hidden";
  return () => {
    document.body.style.overflow = "auto";
  };
  }, []);

  // 프로필 체크
  useEffect(() => {
    const token = localStorage.getItem("accessToken");
    if (!token) return;

    const checkProfile = async () => {
      try {
        const res = await fetch(`${API_BASE}/profile/beauty`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();
        if (!data.success || !data.profile) {
          setShowProfilePopup(true);
        }
      } catch (err) {
        console.error("프로필 조회 실패:", err);
      }
    };

    checkProfile();
  }, []);

  return (
    <div className="Home_wrap container2">

      {showProfilePopup && (
        <div className="profile-modal-overlay">
          <div className="profile-modal">
            <h2>프로필이 아직 없어요!</h2>
            <p>맞춤 제품 추천을 위해<br/>프로필을 먼저 설정해주세요 💄✨</p>

            <button
              className="profile-modal-btn"
              onClick={() => navigate("/profilesetting")}
            >
              프로필 설정하러 가기
            </button>
          </div>
        </div>
      )}

      {/* 상단 인사 + 유저 아이콘 */}
      <header className="home-header">
        <div className="greeting">
          <h2><span className="username">{username || "사용자"}</span>님 안녕하세요!</h2>
          <p>VIZY가 오늘의 메이크업 컬러를 찾아드릴게요 ✨</p>
        </div>

        {/* 🔥 메뉴 대신 유저 아이콘으로 변경 */}
        <button 
          className="menu-btn"
          onClick={() => navigate("/profileview")}
        >
          <FiUser />
        </button>
      </header>

      {/* 카드 슬라이드 */}
      <section className="card-section">
        <Swiper
          modules={[Pagination, Autoplay]}
          pagination={{ clickable: true }}
          autoplay={{ delay: 3000, disableOnInteraction: false }}
          loop={true}
          spaceBetween={20}
          slidesPerView={1}
          className="home-swiper"
        >
          <SwiperSlide><div className="card"><img src={Card1} alt="" className="card-logo" /></div></SwiperSlide>
          <SwiperSlide><div className="card"><img src={Card2} alt="" className="card-logo" /></div></SwiperSlide>
          <SwiperSlide><div className="card"><img src={Card3} alt="" className="card-logo" /></div></SwiperSlide>
        </Swiper>
      </section>

      {/* 버튼 */}
      <div className="button-area">
        <button className="btn btn-face" onClick={() => navigate("/mainface")}>
          👱‍♀️ 얼굴 이미지로 제품 찾기
        </button>

        <button className="btn btn-product" onClick={() => navigate("/mainproduct")}>
          💬 제품 이미지로 추천받기
        </button>
      </div>
    </div>
  );
};

export default Home;
