import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FiSend, FiChevronLeft, FiHome } from "react-icons/fi";
import "../assets/sass/chat/chat.scss";
import ChatLogo from "../assets/img/chat/chatbot_lg.svg";
import VizyIcon from "../assets/img/chat/chatbot_icon.svg";

const API_BASE = "https://pythonapi-production-8efe.up.railway.app";  // 🐍 RAG/에이전트
const NODE_API = "https://genaiproject-production.up.railway.app/api"; // 🟢 유저/프로필

const ChatBot = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [showDeleteBtn, setShowDeleteBtn] = useState(false);

  // 🔥 여기서 진짜 프로필을 관리
  const [userBasic, setUserBasic] = useState(null);   // { id, email, username ... }
  const [userBeauty, setUserBeauty] = useState(null); // { skin_undertone, preferred_finish ... }
  const [isProfileLoading, setIsProfileLoading] = useState(true);

  const navigate = useNavigate();
  const bottomRef = useRef(null);

  // ✅ 1) 최초 진입 시 localStorage + NODE_API에서 프로필 로드
  useEffect(() => {
    const tk = localStorage.getItem("accessToken");

    // 1) localStorage에 저장된 값 먼저 읽기 (ProfileView에서 저장해둔 것)
    const basicStr = localStorage.getItem("user_basic");
    const beautyStr = localStorage.getItem("user_beauty");

    if (basicStr) {
      try {
        setUserBasic(JSON.parse(basicStr));
      } catch (e) {
        console.warn("user_basic JSON parse 실패", e);
      }
    }
    if (beautyStr) {
      try {
        setUserBeauty(JSON.parse(beautyStr));
      } catch (e) {
        console.warn("user_beauty JSON parse 실패", e);
      }
    }

    // 2) 토큰 있으면 Node API에서 한 번 더 최신 프로필 가져오기
    if (!tk) {
      console.warn("⚠ accessToken 없음 → 게스트 모드로 동작");
      setIsProfileLoading(false);
      return;
    }

    const fetchUserInfo = async () => {
      try {
        const res = await fetch(`${NODE_API}/auth/profile`, {
          headers: { Authorization: `Bearer ${tk}` },
        });
        const data = await res.json();
        if (res.ok && data.user) {
          setUserBasic(data.user);
          localStorage.setItem("user_basic", JSON.stringify(data.user));
        }
      } catch (err) {
        console.error("auth/profile 불러오기 실패:", err);
      }
    };

    const fetchBeautyProfile = async () => {
      try {
        const res = await fetch(`${NODE_API}/profile/beauty`, {
          headers: { Authorization: `Bearer ${tk}` },
        });
        const data = await res.json();
        if (res.ok && data.profile) {
          setUserBeauty(data.profile);
          localStorage.setItem("user_beauty", JSON.stringify(data.profile));
        }
      } catch (err) {
        console.error("profile/beauty 불러오기 실패:", err);
      }
    };

    Promise.all([fetchUserInfo(), fetchBeautyProfile()]).finally(() => {
      setIsProfileLoading(false);
    });

    document.body.style.overflow = "hidden";
    return () => (document.body.style.overflow = "auto");
  }, []);

  // ✅ 2) Python 에이전트 호출
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setInput("");

    // 디버깅용 로그
    console.log("🧵 에이전트 호출에 사용될 프로필:", {
      userBasic,
      userBeauty,
    });

    try {
      const res = await fetch(`${API_BASE}/api/agent/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userBasic?.id || userBasic?.email || "guest",
          message: userMessage,
          current_recommendations: [],
          category: "lips",

          // 👉 여기서 Request Example 구조 맞춰서 보냄
          user_profile: {
            tone: userBeauty?.skin_undertone || null, // 예: "cool" / "warm" / "neutral"
            fav_brands: userBeauty?.preferred_store
              ? [userBeauty.preferred_store]
              : [],
            finish_preference: userBeauty?.preferred_finish
              ? [userBeauty.preferred_finish]
              : [],
            price_range:
              userBeauty?.price_range_min != null &&
              userBeauty?.price_range_max != null
                ? [userBeauty.price_range_min, userBeauty.price_range_max]
                : [],
          },
        }),
      });

      const data = await res.json();

      console.log("🧠 Agent 응답:", data);

      if (data.success) {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: data.assistant_message,
            products: data.recommendations || [],
          },
        ]);
      } else {
        throw new Error("Agent error");
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "🚨 서버와 통신할 수 없습니다." },
      ]);
    }
  };

  // ✅ 3) 메모리 삭제 (Python memory/clear 연동)
  const handleClearChat = async () => {
    const USER_ID = userBasic?.id || userBasic?.email || "guest";

    try {
      const res = await fetch(`${API_BASE}/api/memory/clear/${USER_ID}`, {
        method: "DELETE",
      });
      const data = await res.json();

      if (data.success) {
        setMessages([]);
        setShowDeleteBtn(false);
        alert(`기록 ${data.deleted_count}개가 삭제되었습니다.`);
      } else {
        alert("삭제 실패");
      }
    } catch (err) {
      console.error("메모리 삭제 실패:", err);
      alert("서버와 통신 오류");
    }
  };

  // ✅ 4) 봇 응답이 오면 삭제 버튼 표시
  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === "bot") {
      setShowDeleteBtn(true);
    }
  }, [messages]);

  // ✅ 5) 자동 스크롤
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="container2">
      <div className="ChatBot_wrap">
        <header className="cb-topbar">
          <button className="cb-back-btn" onClick={() => window.history.back()}>
            <FiChevronLeft />
          </button>
          <button className="cb-home-btn" onClick={() => navigate("/home")}>
            <FiHome />
          </button>
        </header>

        <div className="cb-header">
          <img src={ChatLogo} alt="VIZY Logo" className="cb-logo" />
          <p className="cb-title">Ask VIZY Assistant anything</p>
        </div>

        {/* 프로필 아직 로딩 중이면 안내 문구 (선택사항) */}
        {isProfileLoading && (
          <div className="cb-profile-hint">
            프로필 정보를 불러오는 중입니다...
          </div>
        )}

        <div className="cb-body">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`cb-msg-row ${msg.role === "user" ? "user" : "bot"}`}
            >
              {msg.role === "bot" && (
                <div className="cb-avatar">
                  <img src={VizyIcon} alt="VZ" />
                </div>
              )}

              <div className="cb-msg-container">
                <div className={`cb-msg-bubble ${msg.role}`}>{msg.text}</div>

                {msg.products && msg.products.length > 0 && (
                  <div className="cb-product-list horizontal">
                    {msg.products.map((p, idx) => (
                      <div key={idx} className="cb-product-card">
                        <strong>{p.brand}</strong>
                        <p>{p.product_name}</p>
                        <p>{p.shade_name}</p>
                        <p>{p.finish}</p>
                        <p>{p.price?.toLocaleString()}원</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {showDeleteBtn && (
            <div className="cb-clear-wrapper">
              <button className="cb-clear-btn" onClick={handleClearChat}>
                대화 내용 삭제하기
              </button>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="cb-bottom">
          {messages.length === 0 && (
            <div className="cb-bot-row">
              <div className="cb-avatar">
                <img src={VizyIcon} alt="VIZY" />
              </div>
              <div className="cb-bubble">
                <p className="cb-bubble-main">무엇이든 물어보세요!</p>
                <p className="cb-bubble-sub">
                  당신만을 위한 VIZY beauty stylist 입니다.
                </p>
              </div>
            </div>
          )}

          <form className="cb-input-row" onSubmit={handleSubmit}>
            <input
              className="cb-input"
              type="text"
              placeholder="궁금한 점을 입력해주세요."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" className="cb-send-btn">
              <FiSend />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatBot;
