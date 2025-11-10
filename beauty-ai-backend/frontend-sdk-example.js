// frontend-sdk-example.js
const API_BASE = "https://genaiproject-production.up.railway.app/api";

const testUser = {
  email: "test@example.com",
  password: "Password123!"
};

async function testHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    console.log("Server health:", data);
  } catch (err) {
    console.error("Server connection failed:", err);
  }
}

async function testLogin() {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(testUser)
    });

    const data = await res.json();
    console.log("Login response:", data);

    if (data.success) {
      console.log("Login successful.");
      console.log("Access Token:", data.accessToken);
      console.log("Refresh Token:", data.refreshToken);
    } else {
      console.log("Login failed:", data.message);
    }
  } catch (err) {
    console.error("Network error:", err);
  }
}

testHealth().then(() => testLogin());
