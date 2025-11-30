// src/pages/profile/ProfileView.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../assets/sass/profile/profileview.scss";
import { FiChevronLeft } from "react-icons/fi";

const NODE_API = "https://genaiproject-production.up.railway.app/api";

export default function ProfileView() {
  const navigate = useNavigate();
  const [token, setToken] = useState("");

  const [userInfo, setUserInfo] = useState(null);
  const [profile, setProfile] = useState(null);

  const [isLoading, setIsLoading] = useState(true); // 🔥 로딩 상태 추가

  useEffect(() => {
    const tk = localStorage.getItem("accessToken");
    if (!tk) {
      navigate("/login");
      return;
    }

    setToken(tk);

    // 🔥 병렬로 동시에 요청하기
    Promise.all([fetchUserInfo(tk), fetchBeautyProfile(tk)]).then(() => {
      setIsLoading(false); // 🔥 모든 fetch 끝나면 로딩 종료
    });
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "auto";
    };
  }, []);

  // 회원 정보
  const fetchUserInfo = async (tk) => {
    const res = await fetch(`${NODE_API}/auth/profile`, {
      headers: { Authorization: `Bearer ${tk}` },
    });
    const data = await res.json();
    if (res.ok) setUserInfo(data.user);

        localStorage.setItem("user_basic", JSON.stringify(data.user));

  };

  // 뷰티 프로필
  const fetchBeautyProfile = async (tk) => {
    const res = await fetch(`${NODE_API}/profile/beauty`, {
      headers: { Authorization: `Bearer ${tk}` },
    });

    const data = await res.json();
    if (res.ok && data.profile) {
      setProfile(data.profile);
          localStorage.setItem("user_beauty", JSON.stringify(data.profile));

    }
  };

  // userInfo + profile을 localStorage("user")에 머지
  useEffect(() => {
    if (!userInfo) return; // 최소 userInfo는 있어야 저장

    const merged = {
      ...userInfo, // id, email, nickname 등
      tone: profile?.personal_color ?? null,
      fav_brands: profile?.preferred_store ?? [],
      finish_preference: profile?.preferred_finish ?? [],
      price_range:
        profile?.price_range_min != null && profile?.price_range_max != null
          ? [profile.price_range_min, profile.price_range_max]
          : [],
    };

    // 디버깅용
    console.log("🔐 merged user for localStorage:", merged);

    localStorage.setItem("user", JSON.stringify(merged));
  }, [userInfo, profile]);

  return (
    <div className="ProfileView_wrap">
      {/* ======================= 🔥 로딩 팝업 ======================= */}
      {isLoading && (
        <div className="pv-loading-overlay">
          <div className="pv-loading-box">
            <p>프로필 정보를 불러오는 중...</p>
          </div>
        </div>
      )}
      {/* =========================================================== */}

      {!isLoading && (
        <>
          <div className="pv-topbar">
            <button className="pv-back-btn" onClick={() => navigate("/home")}>
              <FiChevronLeft size={26} />
            </button>
            <h2>내 프로필</h2>
          </div>

          <div className="pv-content">
            <div className="pv-section">
              <h3>회원 정보</h3>
              <div className="pv-item">
                <label>아이디</label>
                <p>{userInfo.username}</p>
              </div>
              <div className="pv-item">
                <label>이메일</label>
                <p>{userInfo.email}</p>
              </div>
            </div>

            <div className="pv-section">
              <h3>뷰티 프로필</h3>

              <div className="pv-item">
                <label>퍼스널 컬러</label>
                <p>{profile.personal_color}</p>
              </div>
              <div className="pv-item">
                <label>언더톤</label>
                <p>{profile.skin_undertone}</p>
              </div>
              <div className="pv-item">
                <label>피부 타입</label>
                <p>{profile.skin_type}</p>
              </div>
              <div className="pv-item">
                <label>명암 대비</label>
                <p>{profile.contrast_level}</p>
              </div>
              <div className="pv-item">
                <label>선호 피니시</label>
                <p>{profile.preferred_finish}</p>
              </div>
              <div className="pv-item">
                <label>선호 매장</label>
                <p>{profile.preferred_store}</p>
              </div>

              <div className="pv-item">
                <label>가격대</label>
                <p>
                  {profile.price_range_min !== null &&
                  profile.price_range_max !== null
                    ? `${profile.price_range_min} ~ ${profile.price_range_max}원`
                    : "설정 안 함"}
                </p>
              </div>
            </div>

            <button
              className="pv-edit-btn"
              onClick={() => navigate("/profileedit")}
            >
              프로필 수정하기
            </button>
          </div>
        </>
      )}
    </div>
  );
}
