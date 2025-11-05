// src/pages/Home.jsx
import React from "react";
import "../assets/sass/home/home.scss";
import { FiMenu } from "react-icons/fi";
import { Swiper, SwiperSlide } from "swiper/react";
import { Pagination, Autoplay } from "swiper/modules";
import "swiper/css";
import "swiper/css/pagination";

// 카드 이미지들
import Card1 from "../../src/assets/img/card1.svg"
import Card2 from "../../src/assets/img/card2.svg";
import Card3 from "../../src/assets/img/card3.svg";

const Home = () => {
  return (
    <div className="Home_wrap container2">
      {/* 상단 인사 영역 */}
      <header className="home-header">
        <div className="greeting">
          <h2>
            <span className="username">OOO</span>님 안녕하세요!
          </h2>
          <p>VIZY가 오늘의 메이크업 컬러를 찾아드릴게요 ✨</p>
        </div>
        <button className="menu-btn">
          <FiMenu />
        </button>
      </header>

      {/* 카드 슬라이드 영역 */}
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
          <SwiperSlide>
            <div className="card">
              <img src={Card1} alt="카드1" className="card-logo" />
            </div>
          </SwiperSlide>

          <SwiperSlide>
            <div className="card">
              <img src={Card2} alt="카드2" className="card-logo" />
            </div>
          </SwiperSlide>

          <SwiperSlide>
            <div className="card">
              <img src={Card3} alt="카드3" className="card-logo" />
            </div>
          </SwiperSlide>
        </Swiper>
      </section>

      {/* 버튼 영역 */}
      <div className="button-area">
        <button className="btn btn-face">
          <span role="img" aria-label="face">👱‍♀️</span> 얼굴 이미지로 제품 찾기
        </button>

        <button className="btn btn-product">
          <span role="img" aria-label="chat">💬</span> 제품 이미지로 추천받기
        </button>
      </div>
    </div>
  );
};

export default Home;
