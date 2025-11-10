const baseURL = 'https://genaiproject-production.up.railway.app';

const testRegister = async () => {
  console.log('\n=== 회원가입 테스트 ===');
  try {
    const response = await fetch(`${baseURL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: 'testuser',
        email: 'test@example.com',
        password: 'Password123!'
      })
    });
    const data = await response.json();
    console.log('응답:', JSON.stringify(data, null, 2));
    return data.data?.tokens;
  } catch (error) {
    console.error('에러:', error.message);
  }
};

const testLogin = async () => {
  console.log('\n=== 로그인 테스트 ===');
  try {
    const response = await fetch(`${baseURL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'Password123!'
      })
    });
    const data = await response.json();
    console.log('응답:', JSON.stringify(data, null, 2));
    return data.data?.tokens;
  } catch (error) {
    console.error('에러:', error.message);
  }
};

const testProfile = async (accessToken) => {
  console.log('\n=== 프로필 조회 테스트 ===');
  try {
    const response = await fetch(`${baseURL}/api/auth/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });
    const data = await response.json();
    console.log('응답:', JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('에러:', error.message);
  }
};

const testLogout = async (refreshToken) => {
  console.log('\n=== 로그아웃 테스트 ===');
  try {
    const response = await fetch(`${baseURL}/api/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken })
    });
    const data = await response.json();
    console.log('응답:', JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('에러:', error.message);
  }
};

const runTests = async () => {
  console.log('서버가 실행 중인지 확인하세요.');
  console.log('테스트를 시작합니다...\n');

  const registerTokens = await testRegister();
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const loginTokens = await testLogin();
  
  if (loginTokens?.accessToken) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    await testProfile(loginTokens.accessToken);
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    await testLogout(loginTokens.refreshToken);
  }
  
  console.log('\n=== 테스트 완료 ===\n');
};

runTests();
