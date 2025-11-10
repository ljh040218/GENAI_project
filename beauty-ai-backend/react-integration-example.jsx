import React, { useState } from "react";

const API_BASE = "https://genaiproject-production.up.railway.app/api";

export default function App() {
  const [email, setEmail] = useState("test@example.com");
  const [password, setPassword] = useState("Password123!");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      setResult(data);
      console.log("Login response:", data);
    } catch (err) {
      console.error("Network error:", err);
      setResult({ success: false, message: "Network error" });
    }
    setLoading(false);
  };

  const handleHealth = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setResult(data);
      console.log("Health response:", data);
    } catch (err) {
      console.error("Network error:", err);
      setResult({ success: false, message: "Network error" });
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h2>Backend API Connection Test</h2>
      <div>
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
        <button onClick={handleLogin} disabled={loading}>
          {loading ? "Testing..." : "Test Login"}
        </button>
        <button onClick={handleHealth} disabled={loading} style={{ marginLeft: "0.5rem" }}>
          {loading ? "Testing..." : "Test Health"}
        </button>
      </div>
      <pre style={{ background: "#f2f2f2", marginTop: "1rem", padding: "1rem" }}>
        {result ? JSON.stringify(result, null, 2) : "결과가 여기에 표시됩니다."}
      </pre>
    </div>
  );
}
