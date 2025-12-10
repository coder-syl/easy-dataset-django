/**
 * 测试 Django API 是否正常运行
 * 使用方法: node scripts/test-django-api.js
 */

const djangoApiBase = 'http://127.0.0.1:8000';
const projectId = '9dik6qMVfQO0';

async function testDjangoAPI() {
  console.log('🧪 Testing Django API...\n');
  
  // 测试 1: 检查 Django 是否运行
  console.log('1️⃣  Testing if Django is running...');
  try {
    const healthCheck = await fetch(`${djangoApiBase}/api/projects/`);
    console.log(`   ✅ Django is running (Status: ${healthCheck.status})`);
  } catch (error) {
    console.error(`   ❌ Django is NOT running: ${error.message}`);
    console.error(`   💡 Please start Django: cd easy-dataset-django && python manage.py runserver 0.0.0.0:8000`);
    process.exit(1);
  }
  
  // 测试 2: 检查项目是否存在
  console.log('\n2️⃣  Testing if project exists...');
  try {
    const projectResponse = await fetch(`${djangoApiBase}/api/projects/${projectId}/`);
    if (projectResponse.ok) {
      console.log(`   ✅ Project ${projectId} exists`);
    } else {
      console.error(`   ❌ Project ${projectId} not found (Status: ${projectResponse.status})`);
      const errorText = await projectResponse.text();
      console.error(`   Response: ${errorText.substring(0, 200)}`);
    }
  } catch (error) {
    console.error(`   ❌ Error checking project: ${error.message}`);
  }
  
  // 测试 3: 检查 model-config 路由（不带尾部斜杠）
  console.log('\n3️⃣  Testing model-config route (without trailing slash)...');
  try {
    const url1 = `${djangoApiBase}/api/projects/${projectId}/model-config`;
    console.log(`   Requesting: ${url1}`);
    const response1 = await fetch(url1);
    console.log(`   Status: ${response1.status}`);
    if (response1.ok) {
      const data = await response1.json();
      console.log(`   ✅ Success! Response: ${JSON.stringify(data).substring(0, 100)}...`);
    } else {
      const errorText = await response1.text();
      console.error(`   ❌ Failed! Response: ${errorText.substring(0, 200)}`);
    }
  } catch (error) {
    console.error(`   ❌ Error: ${error.message}`);
  }
  
  // 测试 4: 检查 model-config 路由（带尾部斜杠）
  console.log('\n4️⃣  Testing model-config route (with trailing slash)...');
  try {
    const url2 = `${djangoApiBase}/api/projects/${projectId}/model-config/`;
    console.log(`   Requesting: ${url2}`);
    const response2 = await fetch(url2);
    console.log(`   Status: ${response2.status}`);
    if (response2.ok) {
      const data = await response2.json();
      console.log(`   ✅ Success! Response: ${JSON.stringify(data).substring(0, 100)}...`);
    } else {
      const errorText = await response2.text();
      console.error(`   ❌ Failed! Response: ${errorText.substring(0, 200)}`);
    }
  } catch (error) {
    console.error(`   ❌ Error: ${error.message}`);
  }
  
  console.log('\n✨ Test completed!');
}

testDjangoAPI().catch(console.error);

