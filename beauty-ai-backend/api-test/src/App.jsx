import React, { useState } from "react";

const API_BASE = "https://genaiproject-production.up.railway.app/api";

export default function App() {
  const [email, setEmail] = useState("test@example.com");
  const [username, setUsername] = useState("testuser");
  const [password, setPassword] = useState("Password123!");
  const [token, setToken] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

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

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h2>Backend API Connection Test</h2>

      <div style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          style={{ marginRight: "0.5rem" }}
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          style={{ marginRight: "0.5rem" }}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          style={{ marginRight: "0.5rem" }}
        />
      </div>

      <div>
        <button onClick={handleHealth} disabled={loading}>
          Test Health
        </button>
        <button onClick={handleRegister} disabled={loading} style={{ marginLeft: "0.5rem" }}>
          Register
        </button>
        <button onClick={handleLogin} disabled={loading} style={{ marginLeft: "0.5rem" }}>
          Login
        </button>
        <button onClick={handleProfile} disabled={loading} style={{ marginLeft: "0.5rem" }}>
          Get Profile
        </button>
      </div>

      <div style={{ marginTop: "1rem" }}>
        <p>
          <b>Access Token:</b>{" "}
          <span style={{ wordBreak: "break-all", color: "green" }}>
            {token || "(없음)"}
          </span>
        </p>
      </div>

      <pre
        style={{
          background: "#f2f2f2",
          marginTop: "1rem",
          padding: "1rem",
          borderRadius: "6px",
          fontSize: "0.9rem",
          overflowX: "auto",
        }}
      >
        {result ? JSON.stringify(result, null, 2) : "결과가 여기에 표시됩니다."}
      </pre>
    </div>
  );
}