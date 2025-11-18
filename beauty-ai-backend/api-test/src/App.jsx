import React, { useState } from "react";

const NODE_API = "https://genaiproject-production.up.railway.app/api";
const PYTHON_API = "https://pythonapi-production-8efe.up.railway.app";

function labToRGB(L, a, b) {
  let y = (L + 16) / 116;
  let x = a / 500 + y;
  let z = y - b / 200;

  x = 0.95047 * ((x * x * x > 0.008856) ? x * x * x : (x - 16/116) / 7.787);
  y = 1.00000 * ((y * y * y > 0.008856) ? y * y * y : (y - 16/116) / 7.787);
  z = 1.08883 * ((z * z * z > 0.008856) ? z * z * z : (z - 16/116) / 7.787);

  let r = x *  3.2406 + y * -1.5372 + z * -0.4986;
  let g = x * -0.9689 + y *  1.8758 + z *  0.0415;
  let bl = x *  0.0557 + y * -0.2040 + z *  1.0570;

  r = (r > 0.0031308) ? (1.055 * Math.pow(r, 1/2.4) - 0.055) : 12.92 * r;
  g = (g > 0.0031308) ? (1.055 * Math.pow(g, 1/2.4) - 0.055) : 12.92 * g;
  bl = (bl > 0.0031308) ? (1.055 * Math.pow(bl, 1/2.4) - 0.055) : 12.92 * bl;

  const red = Math.max(0, Math.min(255, Math.round(r * 255)));
  const green = Math.max(0, Math.min(255, Math.round(g * 255)));
  const blue = Math.max(0, Math.min(255, Math.round(bl * 255)));

  return `rgb(${red}, ${green}, ${blue})`;
}

const PERSONAL_COLORS = {
  'Spring (봄 웜톤)': [
    { value: 'bright_spring', label: 'Bright Spring (브라이트 봄)' },
    { value: 'true_spring', label: 'True Spring (트루 봄)' },
    { value: 'light_spring', label: 'Light Spring (라이트 봄)' }
  ],
  'Summer (여름 쿨톤)': [
    { value: 'light_summer', label: 'Light Summer (라이트 여름)' },
    { value: 'true_summer', label: 'True Summer (트루 여름)' },
    { value: 'soft_summer', label: 'Soft Summer (소프트 여름)' }
  ],
  'Autumn (가을 웜톤)': [
    { value: 'soft_autumn', label: 'Soft Autumn (소프트 가을)' },
    { value: 'true_autumn', label: 'True Autumn (트루 가을)' },
    { value: 'deep_autumn', label: 'Deep Autumn (딥 가을)' }
  ],
  'Winter (겨울 쿨톤)': [
    { value: 'deep_winter', label: 'Deep Winter (딥 겨울)' },
    { value: 'true_winter', label: 'True Winter (트루 겨울)' },
    { value: 'bright_winter', label: 'Bright Winter (브라이트 겨울)' }
  ]
};

export default function App() {
  const [username, setUsername] = useState("testuser");
  const [email, setEmail] = useState("test@example.com");
  const [password, setPassword] = useState("Password123!");
  const [token, setToken] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const [personalColor, setPersonalColor] = useState("bright_spring");
  const [skinUndertone, setSkinUndertone] = useState("warm");
  const [skinType, setSkinType] = useState("");
  const [contrastLevel, setContrastLevel] = useState("");
  const [preferredFinish, setPreferredFinish] = useState("");
  const [preferredStore, setPreferredStore] = useState("");
  const [priceRangeMin, setPriceRangeMin] = useState("");
  const [priceRangeMax, setPriceRangeMax] = useState("");

  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);

  const handleRegister = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${NODE_API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
      });

      const data = await res.json();
      setResult(data);

      if (res.ok) {
        alert("회원가입 성공!");
      } else {
        alert(`회원가입 실패: ${data.message}`);
      }
    } catch (err) {
      console.error(err);
      alert("회원가입 실패");
      setResult({ success: false, message: "Network error" });
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${NODE_API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      setResult(data);

      if (data?.accessToken) {
        setToken(data.accessToken);
        alert("로그인 성공!");
      } else {
        alert("로그인 실패");
      }
    } catch (err) {
      console.error(err);
      alert("로그인 실패");
      setResult({ success: false, message: "Network error" });
    } finally {
      setLoading(false);
    }
  };

  const handleProfile = async () => {
    if (!token) {
      alert("로그인 먼저 진행하세요.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${NODE_API}/auth/profile`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setResult({ success: false, message: "Network error" });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBeautyProfile = async () => {
    if (!token) {
      alert("로그인 먼저 진행하세요.");
      return;
    }

    const profileData = {
      personalColor,
      skinUndertone
    };

    if (skinType) profileData.skinType = skinType;
    if (contrastLevel) profileData.contrastLevel = contrastLevel;
    if (preferredFinish) profileData.preferredFinish = preferredFinish;
    if (preferredStore) profileData.preferredStore = preferredStore;
    if (priceRangeMin) profileData.priceRangeMin = parseInt(priceRangeMin);
    if (priceRangeMax) profileData.priceRangeMax = parseInt(priceRangeMax);

    setLoading(true);
    try {
      const res = await fetch(`${NODE_API}/profile/beauty`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
      });

      const data = await res.json();
      setResult(data);

      if (res.ok) {
        alert("뷰티 프로필 생성 성공!");
      } else {
        alert(`프로필 생성 실패: ${data.message}`);
      }
    } catch (err) {
      console.error(err);
      alert("프로필 생성 실패");
      setResult({ success: false, message: "Network error" });
    } finally {
      setLoading(false);
    }
  };

  const handleGetBeautyProfile = async () => {
    if (!token) {
      alert("로그인 먼저 진행하세요.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${NODE_API}/profile/beauty`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setResult({ success: false, message: "Network error" });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateBeautyProfile = async () => {
    if (!token) {
      alert("로그인 먼저 진행하세요.");
      return;
    }

    const profileData = {
      personalColor,
      skinUndertone
    };

    if (skinType) profileData.skinType = skinType;
    if (contrastLevel) profileData.contrastLevel = contrastLevel;
    if (preferredFinish) profileData.preferredFinish = preferredFinish;
    if (preferredStore) profileData.preferredStore = preferredStore;
    if (priceRangeMin) profileData.priceRangeMin = parseInt(priceRangeMin);
    if (priceRangeMax) profileData.priceRangeMax = parseInt(priceRangeMax);

    setLoading(true);
    try {
      const res = await fetch(`${NODE_API}/profile/beauty`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
      });

      const data = await res.json();
      setResult(data);

      if (res.ok) {
        alert("뷰티 프로필 업데이트 성공!");
      } else {
        alert(`프로필 업데이트 실패: ${data.message}`);
      }
    } catch (err) {
      console.error(err);
      alert("프로필 업데이트 실패");
      setResult({ success: false, message: "Network error" });
    } finally {
      setLoading(false);
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleAnalyzeImage = async () => {
    if (!token) {
      alert("먼저 로그인하세요!");
      return;
    }

    if (!imageFile) {
      alert("이미지를 업로드하세요.");
      return;
    }

    setImageLoading(true);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append("file", imageFile);

      const res = await fetch(`${PYTHON_API}/api/analyze/image`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      const data = await res.json();
      setAnalysisResult(data);

      if (res.ok) {
        alert("이미지 분석 완료!");
      } else {
        alert(`이미지 분석 실패: ${data.detail || data.message}`);
      }
    } catch (err) {
      console.error(err);
      alert("이미지 분석 중 오류 발생");
      setAnalysisResult({ success: false, message: "Network error" });
    } finally {
      setImageLoading(false);
    }
  };

  const fillMinimalProfile = () => {
    setPersonalColor("bright_spring");
    setSkinUndertone("warm");
    setSkinType("");
    setContrastLevel("");
    setPreferredFinish("");
    setPreferredStore("");
    setPriceRangeMin("");
    setPriceRangeMax("");
    alert("최소 필수 필드만 설정되었습니다!");
  };

  const fillFullProfile = () => {
    setPersonalColor("bright_spring");
    setSkinUndertone("warm");
    setSkinType("combination");
    setContrastLevel("medium");
    setPreferredFinish("dewy");
    setPreferredStore("roadshop");
    setPriceRangeMin("10000");
    setPriceRangeMax("30000");
    alert("모든 필드가 설정되었습니다!");
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "1400px", margin: "0 auto" }}>
      <h2 style={{ color: "#ff69b4" }}>K-Beauty AI Backend API Test</h2>

      <div style={sectionStyle}>
        <h3>1. 인증 (Authentication)</h3>
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
          <button onClick={handleRegister} disabled={loading} style={buttonStyle}>
            회원가입
          </button>
          <button onClick={handleLogin} disabled={loading} style={primaryButtonStyle}>
            로그인
          </button>
          <button onClick={handleProfile} disabled={loading} style={buttonStyle}>
            내 프로필
          </button>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <p>
            <b>Access Token:</b>{" "}
            <span style={{ wordBreak: "break-all", color: token ? "green" : "red", fontSize: "0.85rem" }}>
              {token || "(없음 - 로그인 필요)"}
            </span>
          </p>
        </div>
      </div>

      <div style={{ ...sectionStyle, backgroundColor: "#fff5f7" }}>
        <h3>2. 뷰티 프로필 (Beauty Profile)</h3>
        
        <div style={{ marginBottom: "1rem", padding: "1rem", backgroundColor: "#ffe4e1", borderRadius: "8px" }}>
          <p style={{ margin: 0, fontSize: "0.9rem" }}>
            <b>⚠️ 필수 필드:</b> 퍼스널 컬러, 피부 언더톤 (2개만)<br/>
            <b>💡 선택 필드:</b> 나머지는 입력하지 않아도 됩니다
          </p>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <button onClick={fillMinimalProfile} style={{ ...buttonStyle, backgroundColor: "#90EE90" }}>
            최소 필드만 채우기
          </button>
          <button onClick={fillFullProfile} style={{ ...buttonStyle, backgroundColor: "#87CEEB" }}>
            전체 필드 채우기
          </button>
        </div>
        
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1.5rem" }}>
          
          <div>
            <label style={labelStyle}>
              <b>퍼스널 컬러 (Personal Color)</b> <span style={{ color: "red" }}>* 필수</span>
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
              <b>피부 언더톤 (Skin Undertone)</b> <span style={{ color: "red" }}>* 필수</span>
            </label>
            <select 
              value={skinUndertone} 
              onChange={(e) => setSkinUndertone(e.target.value)}
              style={selectStyle}
            >
              <option value="warm">Warm (웜톤)</option>
              <option value="cool">Cool (쿨톤)</option>
              <option value="neutral">Neutral (중성톤)</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>피부 타입 (Skin Type)</b> <span style={{ color: "#888" }}>선택</span>
            </label>
            <select 
              value={skinType} 
              onChange={(e) => setSkinType(e.target.value)}
              style={selectStyle}
            >
              <option value="">-- 선택 안 함 --</option>
              <option value="oily">Oily (지성)</option>
              <option value="dry">Dry (건성)</option>
              <option value="combination">Combination (복합성)</option>
              <option value="sensitive">Sensitive (민감성)</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>명암 대비 (Contrast Level)</b> <span style={{ color: "#888" }}>선택</span>
            </label>
            <select 
              value={contrastLevel} 
              onChange={(e) => setContrastLevel(e.target.value)}
              style={selectStyle}
            >
              <option value="">-- 선택 안 함 --</option>
              <option value="high">High (높음)</option>
              <option value="medium">Medium (중간)</option>
              <option value="low">Low (낮음)</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>선호 피니시 (Preferred Finish)</b> <span style={{ color: "#888" }}>선택</span>
            </label>
            <select 
              value={preferredFinish} 
              onChange={(e) => setPreferredFinish(e.target.value)}
              style={selectStyle}
            >
              <option value="">-- 선택 안 함 --</option>
              <option value="matte">Matte (매트)</option>
              <option value="glossy">Glossy (글로시)</option>
              <option value="satin">Satin (새틴)</option>
              <option value="velvet">Velvet (벨벳)</option>
              <option value="dewy">Dewy (촉촉)</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>
              <b>선호 매장 (Preferred Store)</b> <span style={{ color: "#888" }}>선택</span>
            </label>
            <select 
              value={preferredStore} 
              onChange={(e) => setPreferredStore(e.target.value)}
              style={selectStyle}
            >
              <option value="">-- 선택 안 함 --</option>
              <option value="roadshop">Roadshop (로드샵)</option>
              <option value="department">Department (백화점)</option>
              <option value="online">Online (온라인)</option>
              <option value="luxury">Luxury (럭셔리)</option>
            </select>
          </div>

          <div style={{ gridColumn: "1 / -1" }}>
            <label style={labelStyle}>
              <b>가격대 (Price Range)</b> <span style={{ color: "#888" }}>선택</span>
            </label>
            <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
              <input
                type="number"
                value={priceRangeMin}
                onChange={(e) => setPriceRangeMin(e.target.value)}
                placeholder="최소 금액 (선택)"
                style={{ ...inputStyle, width: "200px" }}
              />
              <span>~</span>
              <input
                type="number"
                value={priceRangeMax}
                onChange={(e) => setPriceRangeMax(e.target.value)}
                placeholder="최대 금액 (선택)"
                style={{ ...inputStyle, width: "200px" }}
              />
              <span>원</span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: "1.5rem" }}>
          <button onClick={handleCreateBeautyProfile} disabled={loading} style={primaryButtonStyle}>
            뷰티 프로필 생성
          </button>
          <button onClick={handleGetBeautyProfile} disabled={loading} style={buttonStyle}>
            프로필 조회
          </button>
          <button onClick={handleUpdateBeautyProfile} disabled={loading} style={buttonStyle}>
            프로필 업데이트
          </button>
        </div>
      </div>

      <div style={{ ...sectionStyle, backgroundColor: "#f0f8ff" }}>
        <h3>3. 이미지 분석 & 제품 추천</h3>
        <div style={{ marginBottom: "1rem" }}>
          <label style={labelStyle}>
            <b>메이크업 이미지 업로드</b>
          </label>
          <input 
            type="file" 
            accept="image/*" 
            onChange={handleImageChange}
            style={{ ...inputStyle, width: "300px" }}
          />
          {imageFile && (
            <span style={{ marginLeft: "1rem", color: "green" }}>
              선택된 파일: {imageFile.name}
            </span>
          )}
        </div>

        {imagePreview && (
          <div style={{ marginBottom: "1.5rem" }}>
            <label style={labelStyle}>
              <b>이미지 미리보기</b>
            </label>
            <div style={{ border: "2px solid #ddd", borderRadius: "8px", padding: "1rem", display: "inline-block" }}>
              <img 
                src={imagePreview} 
                alt="Preview" 
                style={{ maxWidth: "400px", maxHeight: "400px", display: "block" }}
              />
            </div>
          </div>
        )}

        <button onClick={handleAnalyzeImage} disabled={imageLoading} style={primaryButtonStyle}>
          {imageLoading ? "분석 중..." : "이미지 분석 & 추천 받기"}
        </button>

        {analysisResult && (
          <div style={{ marginTop: "1.5rem" }}>
            <h4>분석 결과</h4>
            
            {analysisResult.success && (
              <>
                {['lips', 'cheeks', 'eyeshadow'].map((category) => {
                  const data = analysisResult[category];
                  if (!data) return null;

                  const categoryNames = {
                    lips: '립',
                    cheeks: '치크',
                    eyeshadow: '아이섀도우'
                  };

                  return (
                    <div key={category} style={categoryResultStyle}>
                      <h3 style={{ color: '#ff69b4', marginBottom: '1rem' }}>
                        {categoryNames[category]} 추천 제품
                      </h3>

                      <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
                        <h4 style={{ marginBottom: '0.5rem' }}>추출된 색상 정보</h4>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                          <div style={{
                            width: '80px',
                            height: '80px',
                            backgroundColor: labToRGB(
                              data.color.lab_standard[0],
                              data.color.lab_standard[1],
                              data.color.lab_standard[2]
                            ),
                            border: '2px solid #ddd',
                            borderRadius: '8px'
                          }}></div>
                          <div style={{ fontSize: '0.9rem' }}>
                            <p><b>LAB (Standard):</b> L={data.color.lab_standard[0].toFixed(1)}, a={data.color.lab_standard[1].toFixed(1)}, b={data.color.lab_standard[2].toFixed(1)}</p>
                            <p><b>Tone Group:</b> {data.color.tone_group}</p>
                            <p><b>Hue:</b> {data.color.hue.toFixed(2)}°</p>
                            <p><b>Chroma:</b> {data.color.chroma.toFixed(2)}</p>
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                        {data.recommendations.map((product, idx) => (
                          <div key={product.id} style={productCardStyle}>
                            <div style={{ position: 'relative' }}>
                              <div style={{
                                position: 'absolute',
                                top: '10px',
                                left: '10px',
                                backgroundColor: '#ff69b4',
                                color: 'white',
                                padding: '4px 12px',
                                borderRadius: '20px',
                                fontWeight: 'bold',
                                fontSize: '0.9rem'
                              }}>
                                {idx + 1}위
                              </div>
                              <img 
                                src={product.image_url} 
                                alt={product.name}
                                style={{
                                  width: '100%',
                                  height: '200px',
                                  objectFit: 'cover',
                                  borderRadius: '8px 8px 0 0'
                                }}
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'flex';
                                }}
                              />
                              <div style={{
                                display: 'none',
                                width: '100%',
                                height: '200px',
                                backgroundColor: '#f0f0f0',
                                alignItems: 'center',
                                justifyContent: 'center',
                                borderRadius: '8px 8px 0 0',
                                color: '#999'
                              }}>
                                이미지 없음
                              </div>
                            </div>
                            
                            <div style={{ padding: '1rem' }}>
                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                marginBottom: '0.5rem'
                              }}>
                                <div style={{
                                  width: '30px',
                                  height: '30px',
                                  backgroundColor: product.color_hex,
                                  border: '2px solid #ddd',
                                  borderRadius: '50%'
                                }}></div>
                                <span style={{ fontSize: '0.85rem', color: '#666' }}>
                                  ΔE: {product.deltaE.toFixed(2)}
                                </span>
                              </div>
                              
                              <h4 style={{ 
                                fontSize: '0.9rem', 
                                marginBottom: '0.3rem',
                                color: '#333'
                              }}>
                                {product.brand}
                              </h4>
                              
                              <p style={{ 
                                fontSize: '0.85rem', 
                                marginBottom: '0.5rem',
                                color: '#666',
                                lineHeight: '1.4'
                              }}>
                                {product.name}
                              </p>
                              
                              <p style={{ 
                                fontSize: '1rem', 
                                fontWeight: 'bold',
                                color: '#ff69b4'
                              }}>
                                {product.price.toLocaleString()}원
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div style={{ 
                        padding: '1.5rem', 
                        backgroundColor: '#fffbf5', 
                        borderRadius: '8px',
                        border: '1px solid #ffe4cc'
                      }}>
                        <h4 style={{ marginBottom: '1rem', color: '#ff8c00' }}>추천 이유</h4>
                        <p style={{ 
                          lineHeight: '1.8', 
                          whiteSpace: 'pre-line',
                          fontSize: '0.95rem'
                        }}>
                          {data.explanation}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </>
            )}

            {!analysisResult.success && (
              <div style={{ padding: '1rem', backgroundColor: '#fee', borderRadius: '8px', color: '#c00' }}>
                <h4>오류 발생</h4>
                <pre style={preStyle}>
                  {JSON.stringify(analysisResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      <div style={sectionStyle}>
        <h3>API 응답 결과</h3>
        <pre style={preStyle}>
          {result ? JSON.stringify(result, null, 2) : "결과가 여기에 표시됩니다."}
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

const productCardStyle = {
  border: "1px solid #ddd",
  borderRadius: "8px",
  overflow: "hidden",
  backgroundColor: "#fff",
  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
  transition: "transform 0.2s",
  cursor: "pointer"
};

const categoryResultStyle = {
  marginBottom: "2rem",
  padding: "1.5rem",
  backgroundColor: "#fff",
  borderRadius: "12px",
  border: "2px solid #f0f0f0"
};