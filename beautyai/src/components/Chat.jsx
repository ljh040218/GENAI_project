import React, { useState,useEffect,useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { FiSend, FiChevronLeft, FiHome } from "react-icons/fi";
import "../assets/sass/chat/chat.scss";
import ChatLogo from "../assets/img/chat/chatbot_lg.svg";
import VizyIcon from "../assets/img/chat/chatbot_icon.svg";
const API_BASE = "https://pythonapi-production-8efe.up.railway.app";
const user = JSON.parse(localStorage.getItem("user"));
const token = localStorage.getItem("accessToken");


const ChatBot = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]); // 🔥 메시지 리스트 추가
  const navigate = useNavigate();
  const bottomRef = useRef(null);
  const handleSubmit = async (e) => {
  e.preventDefault();
  if (!input.trim()) return;

  const userMessage = input;


  // ✅ UI에 사용자 메시지 먼저 출력
  setMessages((prev) => [...prev, { role: "user", text: userMessage }]); setInput("");

  try {
    const res = await fetch(`${API_BASE}/api/agent/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        user_id: user?.id || user?.email || "guest",
        message: userMessage,
        current_recommendations: [],
        category: "lips",

        user_profile: {
          tone: user?.tone || null,
          fav_brands: user?.fav_brands || [],
          finish_preference: user?.finish_preference || [],
          price_range: user?.price_range || []
        }
      })
    });

    const data = await res.json();

    if (data.success) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: data.assistant_message,
          products: data.recommendations || []
        }
      ]);
    } else {
      throw new Error("Agent error");
    }

  } catch (err) {
    console.error(err);
    setMessages((prev) => [
      ...prev,
      { role: "bot", text: "🚨 서버와 통신할 수 없습니다." }
    ]);
  }
};

  
useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: "smooth" });
}, [messages]);
     useEffect(() => {
        document.body.style.overflow = "hidden";
        return () => (document.body.style.overflow = "auto");
      }, []);

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
        {/* 상단 메시지 */}
        <div className="cb-header">
          <img src={ChatLogo} alt="VIZY Logo" className="cb-logo" />
          <p className="cb-title">Ask VIZY Assistant anything</p>
        </div>

        {/* 중간은 여백 (나중에 대화 로그 영역이 될 자리) */}
        <div className="cb-body">
          {messages.map((msg, i) => (
  <div key={i} className={`cb-msg-row ${msg.role === "user" ? "user" : "bot"}`}>
    
    {msg.role === "bot" && (
      <div className="cb-avatar">
        <img src={VizyIcon} alt="VZ" />
      </div>
    )}

    <div className="cb-msg-container">
      <div className={`cb-msg-bubble ${msg.role}`}>{msg.text}</div>



      {/* ✅ 여기로 이동 */}
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

          <div ref={bottomRef} />
        </div>

        {/* 하단 고정 영역 */}
        <div className="cb-bottom">
          {/* 봇 인트로 말풍선 */}
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

          {/* 입력창 */}
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
