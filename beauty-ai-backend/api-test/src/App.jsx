import React, { useState } from "react";

const API_BASE = "https://genaiproject-production.up.railway.app/api";

const PERSONAL_COLORS = {
  'Spring': [
    { value: 'bright_spring', label: 'Bright Spring (브라이트 봄)' },
    { value: 'true_spring', label: 'True Spring (트루 봄)' },
    { value: 'light_spring', label: 'Light Spring (라이트 봄)' }
  ],
  'Summer': [
    { value: 'light_summer', label: 'Light Summer (라이트 여름)' },
    { value: 'true_summer', label: 'True Summer (트루 여름)' },
    { value: 'soft_summer', label: 'Soft Summer (소프트 여름)' }
  ],
  'Autumn': [
    { value: 'soft_autumn', label: 'Soft Autumn (소프트 가을)' },
    { value: 'true_autumn', label: 'True Autumn (트루 가을)' },
    { value: 'deep_autumn', label: 'Deep Autumn (딥 가을)' }
  ],
  'Winter': [
    { value: 'deep_winter', label: 'Deep Winter (딥 겨울)' },
    { value: 'true_winter', label: 'True Winter (트루 겨울)' },
    { value: 'bright_winter', label: 'Bright Winter (브라이트 겨울)' }
  ]
};

export default function App() {
  const [email, setEmail] = useState("test@example.com");
  const [username, setUsername] = useState("testuser");
  const [password, setPassword] = useState("Password123!");
  const [token, setToken] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const [personalColor, setPersonalColor] = useState("bright_spring");
  const [skinUndertone, setSkinUndertone] = useState("warm");
  const [skinType, setSkinType] = useState("combination");
  const [contrastLevel, setContrastLevel] = useState("medium");
  const [preferredFinish, setPreferredFinish] = useState("dewy");
  const [preferredStore, setPreferredStore] = useState("roadshop");
  const [priceRangeMin, setPriceRangeMin] = useState(10000);
  const [priceRangeMax, setPriceRangeMax] = useState(30000);

  const request = async (path, method = "GET", body = null, headers = {}) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : null,
      });
      const data = await res.json();
      setResult(data);
      console.log(path, data);
      return data;
    } catch (err) {
      console.error("Network error:", err);
      setResult({ success: false, message: "Network error" });
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    await request("/auth/register", "POST", {
      username,
      email,
      password,
    });
  };

  const handleLogin = async () => {
    const data = await request("/auth/login", "POST", { email, password });
    if (data?.accessToken) {
      setToken(data.accessToken);
    }
  };

  const handleProfile = async () => {
    if (!token) {
      setResult({ success: false, message: "로그인 먼저 진행하세요." });
      return;
    }
    await request("/auth/profile", "GET", null, {
      Authorization: `Bearer ${token}`,
    });
  };

  const handleHealth = async () => {
    await request("/health");
  };

  const handleCreateBeautyProfile = async () => {
    if (!token) {
      setResult({ success: false, message: "로그인 먼저 진행하세요." });
      return;
    }
    await request("/profile/beauty", "POST", {
      personalColor,
      skinUndertone,
      skinType,
      contrastLevel,
      preferredFinish,
      preferredStore,
      priceRangeMin: parseInt(priceRangeMin),
      priceRangeMax: parseInt(priceRangeMax)
    }, {
      Authorization: `Bearer ${token}`,
    });
  };

  const handleGetBeautyProfile = async () => {
    if (!token) {
      setResult({ success: false, message: "로그인 먼저 진행하세요." });
      return;
    }
    await request("/profile/beauty", "GET", null, {
      Authorization: `Bearer ${token}`,
    });
  };

  const handleUpdateBeautyProfile = async () => {
    if (!token) {
      setResult({ success: false, message: "로그인 먼저 진행하세요." });
      return;
    }
    await request("/profile/beauty", "PUT", {
      personalColor,
      skinUndertone,
      skinType,
      contrastLevel,
      preferredFinish,
      preferredStore,
      priceRangeMin: parseInt(priceRangeMin),
      priceRangeMax: parseInt(priceRangeMax)
    }, {
      Authorization: `Bearer ${token}`,
    });
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "1400px", margin: "0 auto" }}>
      <h2>K-Beauty AI Backend API Test</h2>

      <div style={sectionStyle}>
        <h3>1. Authentication</h3>
        <div style={{ marginBottom: "1rem" }}>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            style={inputStyle}
          />
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
        </div>

        <div>
          <button onClick={handleHealth} disabled={loading} style={buttonStyle}>
            Health Check
          </button>
          <button onClick={handleRegister} disabled={loading} style={buttonStyle}>
            Register
          </button>
          <button onClick={handleLogin} disabled={loading} style={buttonStyle}>
            Login
          </button>
          <button onClick={handleProfile} disabled={loading} style={buttonStyle}>
            Get User Profile
          </button>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <p>
            <b>Access Token:</b>{" "}
            <span style={{ wordBreak: "break-all", color: token ? "green" : "red", fontSize: "0.85rem" }}>
              {token || "(Please login first)"}
            </span>
          </p>
        </div>
      </div>

      <div style={{ ...sectionStyle, backgroundColor: "#fff5f7" }}>
        <h3>2. Beauty Profile</h3>
        
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1.5rem" }}>
          
          <div>
            <label style={labelStyle}>
              <b>Personal Color</b> <span style={{ color: "red" }}>*</span>
            </label>
            <select 
              value={personalColor} 
              onChange={(e) => setPersonalColor(e.target.value)}
              style={selectStyle}
            >
              {Object.entries(PERSONAL_COLORS).map(([season, colors]) => (
                <optgroup key={season} label={season}>
                  {colors.map(color => (
                    <option key={color.value} value={color.value}>
                      {color.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>Skin Undertone</b> <span style={{ color: "red" }}>*</span>
            </label>
            <select 
              value={skinUndertone} 
              onChange={(e) => setSkinUndertone(e.target.value)}
              style={selectStyle}
            >
              <option value="warm">Warm</option>
              <option value="cool">Cool</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>Skin Type</b> <span style={{ color: "red" }}>*</span>
            </label>
            <select 
              value={skinType} 
              onChange={(e) => setSkinType(e.target.value)}
              style={selectStyle}
            >
              <option value="oily">Oily</option>
              <option value="dry">Dry</option>
              <option value="combination">Combination</option>
              <option value="sensitive">Sensitive</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>Contrast Level</b> <span style={{ color: "red" }}>*</span>
            </label>
            <select 
              value={contrastLevel} 
              onChange={(e) => setContrastLevel(e.target.value)}
              style={selectStyle}
            >
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>Preferred Finish</b> <span style={{ color: "red" }}>*</span>
            </label>
            <select 
              value={preferredFinish} 
              onChange={(e) => setPreferredFinish(e.target.value)}
              style={selectStyle}
            >
              <option value="matte">Matte</option>
              <option value="glossy">Glossy</option>
              <option value="satin">Satin</option>
              <option value="velvet">Velvet</option>
              <option value="dewy">Dewy</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>Preferred Store</b> <span style={{ color: "red" }}>*</span>
            </label>
            <select 
              value={preferredStore} 
              onChange={(e) => setPreferredStore(e.target.value)}
              style={selectStyle}
            >
              <option value="roadshop">Roadshop</option>
              <option value="department">Department</option>
              <option value="online">Online</option>
              <option value="luxury">Luxury</option>
            </select>
          </div>

          <div style={{ gridColumn: "1 / -1" }}>
            <label style={labelStyle}>
              <b>Price Range (KRW)</b>
            </label>
            <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
              <input
                type="number"
                value={priceRangeMin}
                onChange={(e) => setPriceRangeMin(e.target.value)}
                placeholder="Min"
                style={{ ...inputStyle, width: "200px" }}
              />
              <span>~</span>
              <input
                type="number"
                value={priceRangeMax}
                onChange={(e) => setPriceRangeMax(e.target.value)}
                placeholder="Max"
                style={{ ...inputStyle, width: "200px" }}
              />
            </div>
          </div>
        </div>

        <div style={{ marginTop: "1.5rem" }}>
          <button onClick={handleCreateBeautyProfile} disabled={loading} style={primaryButtonStyle}>
            Create Beauty Profile
          </button>
          <button onClick={handleGetBeautyProfile} disabled={loading} style={buttonStyle}>
            Get Beauty Profile
          </button>
          <button onClick={handleUpdateBeautyProfile} disabled={loading} style={buttonStyle}>
            Update Beauty Profile
          </button>
        </div>
      </div>

      <div style={sectionStyle}>
        <h3>API Response</h3>
        <pre style={preStyle}>
          {result ? JSON.stringify(result, null, 2) : "Response will appear here"}
        </pre>
      </div>
    </div>
  );
}

const sectionStyle = {
  border: "1px solid #ddd",
  padding: "1.5rem",
  marginBottom: "1.5rem",
  borderRadius: "8px",
  backgroundColor: "#fff"
};

const inputStyle = {
  marginRight: "0.5rem",
  padding: "0.6rem",
  borderRadius: "4px",
  border: "1px solid #ddd",
  fontSize: "14px"
};

const selectStyle = {
  width: "100%",
  padding: "0.6rem",
  borderRadius: "4px",
  border: "1px solid #ddd",
  fontSize: "14px",
  backgroundColor: "white"
};

const labelStyle = {
  display: "block",
  marginBottom: "0.5rem",
  fontSize: "14px"
};

const buttonStyle = {
  marginLeft: "0.5rem",
  padding: "0.6rem 1.2rem",
  cursor: "pointer",
  backgroundColor: "#fff",
  border: "1px solid #ddd",
  borderRadius: "4px",
  fontSize: "14px"
};

const primaryButtonStyle = {
  ...buttonStyle,
  backgroundColor: "#ff69b4",
  color: "white",
  border: "none",
  fontWeight: "bold"
};

const preStyle = {
  background: "#f2f2f2",
  padding: "1rem",
  borderRadius: "6px",
  fontSize: "0.9rem",
  overflowX: "auto",
  maxHeight: "500px",
  overflowY: "auto"
};