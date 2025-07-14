import axios from 'axios';

// API请求的基本URL
const API_BASE_URL = '/api';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API函数
export const generateTestCases = async (formData) => {
  try {
    console.log('API 服务: 发送请求到后端...');
    console.log('API 服务: 请求数据:', formData);

    // 使用原生 fetch 而不是 axios 来处理流式响应
    const response = await fetch(`${API_BASE_URL}/test-cases/generate`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error('API 服务: 生成测试用例错误:', error);
    throw error;
  }
};

// 生成功能测试点的API函数
export const generateTestPoints = async (formData) => {
  try {
    console.log('API 服务: 发送功能测试点生成请求到后端...');
    console.log('API 服务: 请求数据:', formData);

    // 使用原生 fetch 来处理流式响应
        const response = await fetch(`${API_BASE_URL}/test-cases/generate`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error('API 服务: 生成功能测试点错误:', error);
    throw error;
  }
};

export const exportToExcel = async (testCases) => {
  try {
    const response = await api.post('/test-cases/export', testCases, {
      responseType: 'blob', // 对于文件下载很重要
    });
    return response;
  } catch (error) {
    console.error('Error exporting to Excel:', error);
    throw error;
  }
};

export const generateMindMap = async (testCases) => {
  try {
    console.log('API 服务: 发送思维导图生成请求到后端...');
    console.log('API 服务: 测试用例数据:', testCases);
    
    const response = await api.post('/test-cases/generate-mindmap', {
      test_cases: testCases
    });
    
    console.log('API 服务: 思维导图生成成功:', response.data);
    return response.data;
  } catch (error) {
    console.error('API 服务: 生成思维导图错误:', error);
    throw error;
  }
};

export const pingServer = async () => {
  try {
    console.log('Pinging server...');
    const response = await fetch(`${API_BASE_URL}/ping`);
    const data = await response.json();
    console.log('Ping response:', data);
    return data;
  } catch (error) {
    console.error('Ping error:', error);
    throw error;
  }
};

/**
 * 调用后端进行测试点提取
 * @param {FormData} formData - 原始的PRD文本内容
 * @returns {Promise<Response>} 返回一个Promise，其值为原生的Fetch Response对象，以便上层处理流
 */
export const detectTestPoint = async (formData) => {
  console.log("API: 调用 /test-cases/detect_test_point...");
  try {
    const response = await fetch(`${API_BASE_URL}/test-cases/detect_test_point`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`服务器错误: ${response.status} ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error("API: 测试点提取失败:", error);
    throw error;
  }
};

/**
 * 从服务器获取当前会话中已生成的测试点数据
 * @returns {Promise<Object>} 返回一个Promise，其值为解析后的JSON对象（即测试点数据）
 */
export const getTestPoints = async () => {
  console.log("API: 调用 /get_test_points 获取结构化数据...");

  try {
    // 假设后端提供了一个新的GET接口来获取session中的数据
    // 我们使用axios实例，因为它能自动处理JSON解析
    // 注意：这里我们不再使用fetch，因为不需要处理流
    const response = await api.get('/test-cases/get_test_points');

    // axios会将响应数据直接放在response.data中
    return response.data;

  } catch (error) {
    console.error("API: 获取测试点数据失败:", error);
    throw error;
  }
};

/**
 * 提交对测试点的人工审核意见
 * @param {string} userReview - 用户输入的审核或修改意见
 * @returns {Promise<Response>} 返回Fetch Response对象
 */
export const reviewTestPoint = async (userReview) => {
  console.log("API: 调用 /test_point_review...");

  const formData = new FormData();
  formData.append('user_review', userReview);

  try {
    const response = await fetch(`${API_BASE_URL}/test-cases/test_point_review`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`服务器错误: ${response.status} ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error("API: 测试点审核失败:", error);
    throw error;
  }
};

/**
 * 触发后端根据session中的测试点，开始生成测试用例
 * @returns {Promise<Response>} 返回Fetch Response对象
 */
export const generateTestCase = async () => {
  console.log("API: 调用 /generate_test_case...");

  try {
    // 这个接口不需要发送body，但仍需是POST请求
    const response = await fetch(`${API_BASE_URL}/test-cases/generate_test_case`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`服务器错误: ${response.status} ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error("API: 测试用例生成失败:", error);
    throw error;
  }
};

/**
 * 提交对已生成测试用例的人工审核意见
 * @param {string[]} reviewList - 需要修订的测试用例ID列表
 * @param {string} reviewFunction - 用户输入的对这些用例的统一修订意见
 * @returns {Promise<Response>} 返回Fetch Response对象
 */
export const reviewTestCases = async (reviewList, reviewFunction) => {
  console.log("API: 调用 /test_case_review...");

  const formData = new FormData();

  // 关键：要发送一个列表，需要用同一个键名多次调用append
  reviewList.forEach(item => {
    formData.append('review_list', item);
  });

  formData.append('review_function', reviewFunction);

  try {
    const response = await fetch(`${API_BASE_URL}/test-cases/test_case_review`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`服务器错误: ${response.status} ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error("API: 测试用例审核失败:", error);
    throw error;
  }
};

/**
 * 从服务器获取当前会<seg_1>中所有最新的测试用例
 * @returns {Promise<Array>} 返回一个Promise，其值为测试用例数组
 */
export const getAllTestCases = async () => {
  console.log("API: 获取全部最新的测试用例...");
  try {
    // 使用预配置的axios实例，因为它会帮我们自动解析JSON
    const response = await api.get('/test-cases/all-test-cases');
    return response.data;
  } catch (error) {
    console.error("API: 获取全部测试用例失败:", error);
    throw error;
  }
};

export default api;
