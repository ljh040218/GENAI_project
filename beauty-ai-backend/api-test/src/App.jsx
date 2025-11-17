import React, { useState } from "react";

const API_BASE = "https://genaiproject-production.up.railway.app/api";

export default function ImageAnalysisPage() {
  // Auth 상태
  const [email, setEmail] = useState("test@example.com");
  const [password, setPassword] = useState("Password123!");
  const [token, setToken] = useState("");

  // 이미지 업로드 상태
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  // 응답 / 로딩 / 에러
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState("");

  // 공통 요청 함수 (JSON용)
  const jsonRequest = async (path, method = "GET", body = null, extraHeaders = {}) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...extraHeaders,
        },
        body: body ? JSON.stringify(body) : null,
      });

      const data = await res.json();
      return data;
    } catch (err) {
      console.error("Network error:", err);
      return { success: false, message: "Network error" };
    } finally {
      setLoading(false);
    }
  };

  // 로그인
  const handleLogin = async () => {
    setAuthMessage("");
    const data = await jsonRequest("/auth/login", "POST", { email, password });
    if (data?.accessToken) {
      setToken(data.accessToken);
      setAuthMessage("로그인 성공: 토큰이 설정되었습니다.");
    } else {
      setAuthMessage(data?.message || "로그인 실패");
    }
  };

  // 이미지 선택
  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) {
      setImageFile(null);
      setImagePreview(null);
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  // 이미지 분석 요청
  const handleAnalyzeImage = async () => {
    if (!token) {
      setAnalysisResult({
        success: false,
        message: "먼저 로그인해서 토큰을 받아야 합니다.",
      });
      return;
    }

    if (!imageFile) {
      setAnalysisResult({
        success: false,
        message: "분석할 이미지를 업로드하세요.",
      });
      return;
    }

    setLoading(true);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append("image", imageFile);

      const res = await fetch(`${API_BASE}/image/analyze`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          // multipart/form-data는 브라우저가 boundary 포함해서 알아서 설정하므로
          // "Content-Type" 수동 지정하면 안 됨
        },
        body: formData,
      });

      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      console.error("Image analyze error:", err);
      setAnalysisResult({
        success: false,
        message: "이미지 분석 중 오류가 발생했습니다.",
      });
    } finally {
      setLoading(false);
    }
  };

  // 색상 / 추천 결과 예쁘게 출력 (있으면)
  const renderColors = (colors) => {
    if (!colors || typeof colors !== "object") return null;

    return (
      <div style={{ marginTop: "1rem" }}>
        <h4>추출된 LAB 색상</h4>
        <ul>
          {Object.entries(colors).map(([region, lab]) => (
            <li key={region}>
              <b>{region}</b>:{" "}
              {Array.isArray(lab)
                ? `L=${lab[0]?.toFixed?.(2) ?? lab[0]}, a=${lab[1]?.toFixed?.(
                    2
                  ) ?? lab[1]}, b=${lab[2]?.toFixed?.(2) ?? lab[2]}`
                : JSON.stringify(lab)}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const renderRecommendations = (recs) => {
    if (!recs || typeof recs !== "object") return null;

    return (
      <div style={{ marginTop: "1rem" }}>
        <h4>추천 제품</h4>
        {Object.entries(recs).map(([category, items]) => (
          <div key={category} style={{ marginBottom: "1rem" }}>
            <h5>{category}</h5>
            {Array.isArray(items) && items.length > 0 ? (
              <ul>
                {items.map((item, idx) => (
                  <li key={idx}>
                    <b>{item.brand}</b> - {item.name}{" "}
                    {item.deltaE !== undefined && (
                      <span style={{ fontSize: "0.85rem", color: "#555" }}>
                        (ΔE: {item.deltaE?.toFixed?.(2) ?? item.deltaE})
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: "0.85rem", color: "#777" }}>
                추천 결과가 없습니다.
              </p>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div
      style={{
        padding: "2rem",
        fontFamily: "sans-serif",
        maxWidth: "1200px",
        margin: "0 auto",
      }}
    >
      <h2>K-Beauty AI · 이미지 분석 & 추천</h2>

      {/* 1. 로그인 섹션 */}
      <div style={sectionStyle}>
        <h3>1. 로그인</h3>
        <p style={{ fontSize: "0.9rem", color: "#555" }}>
          JWT 토큰이 있어야 이미지 분석 API를 호출할 수 있습니다.
        </p>
        <div style={{ marginBottom: "1rem" }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            style={inputStyle}
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            style={inputStyle}
          />
          <button onClick={handleLogin} disabled={loading} style={primaryButtonStyle}>
            로그인
          </button>
        </div>
        <div style={{ fontSize: "0.85rem" }}>
          <p>
            <b>Access Token:</b>{" "}
            <span
              style={{
                wordBreak: "break-all",
                color: token ? "green" : "red",
              }}
            >
              {token || "(로그인 필요)"}
            </span>
          </p>
          {authMessage && (
            <p style={{ color: "#444", marginTop: "0.3rem" }}>{authMessage}</p>
          )}
        </div>
      </div>

      {/* 2. 이미지 업로드 & 분석 */}
      <div style={{ ...sectionStyle, backgroundColor: "#fff5f7" }}>
        <h3>2. 이미지 업로드 & 분석</h3>
        <p style={{ fontSize: "0.9rem", color: "#555" }}>
          얼굴이 잘 나온 정면 사진을 업로드하면, 립 / 치크 / 아이섀도우 영역을 분석해서
          LAB 색상과 제품 추천을 반환합니다.
        </p>

        <div style={{ marginTop: "1rem" }}>
          <input
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            style={{ marginBottom: "1rem" }}
          />
        </div>

        {imagePreview && (
          <div style={{ marginTop: "1rem", display: "flex", gap: "1.5rem" }}>
            <div>
              <p style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>업로드한 이미지 미리보기</p>
              <img
                src={imagePreview}
                alt="preview"
                style={{
                  maxWidth: "260px",
                  borderRadius: "8px",
                  border: "1px solid #ddd",
                }}
              />
            </div>
          </div>
        )}

        <div style={{ marginTop: "1.5rem" }}>
          <button
            onClick={handleAnalyzeImage}
            disabled={loading}
            style={primaryButtonStyle}
          >
            {loading ? "분석 중..." : "이미지 분석 & 추천 받기"}
          </button>
        </div>
      </div>

      {/* 3. 결과 출력 */}
      <div style={sectionStyle}>
        <h3>3. 분석 결과</h3>
        {analysisResult ? (
          <>
            {analysisResult.message && (
              <p
                style={{
                  color: analysisResult.success === false ? "red" : "#333",
                }}
              >
                {analysisResult.message}
              </p>
            )}

            {renderColors(analysisResult.colors)}
            {renderRecommendations(analysisResult.recommendations)}

            <h4 style={{ marginTop: "1.5rem" }}>Raw Response</h4>
            <pre style={preStyle}>
              {JSON.stringify(analysisResult, null, 2)}
            </pre>
          </>
        ) : (
          <p style={{ fontSize: "0.9rem", color: "#777" }}>
            아직 분석 결과가 없습니다. 이미지를 업로드하고 분석을 실행해보세요.
          </p>
        )}
      </div>
    </div>
  );
}

const sectionStyle = {
  border: "1px solid #ddd",
  padding: "1.5rem",
  marginBottom: "1.5rem",
  borderRadius: "8px",
  backgroundColor: "#fff",
};

const inputStyle = {
  marginRight: "0.5rem",
  padding: "0.6rem",
  borderRadius: "4px",
  border: "1px solid #ddd",
  fontSize: "14px",
};

const buttonStyle = {
  marginLeft: "0.5rem",
  padding: "0.6rem 1.2rem",
  cursor: "pointer",
  backgroundColor: "#fff",
  border: "1px solid #ddd",
  borderRadius: "4px",
  fontSize: "14px",
};

const primaryButtonStyle = {
  ...buttonStyle,
  backgroundColor: "#ff69b4",
  color: "white",
  border: "none",
  fontWeight: "bold",
};

const preStyle = {
  background: "#f2f2f2",
  padding: "1rem",
  borderRadius: "6px",
  fontSize: "0.9rem",
  overflowX: "auto",
  maxHeight: "500px",
  overflowY: "auto",
};
