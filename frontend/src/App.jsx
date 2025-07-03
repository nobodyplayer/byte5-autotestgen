import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';

import FileDownloadIcon from '@mui/icons-material/FileDownload';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import Header from './components/Header';
import UploadArea from './components/UploadArea';
import TestCaseDisplay from './components/TestCaseDisplay';
import StreamingOutput from './components/StreamingOutput';
import { generateTestCases, pingServer } from './services/api';

// 创建现代化主题，参考 Notion、Linear 等产品设计
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6366f1',
      light: '#818cf8',
      dark: '#4f46e5',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ec4899',
      light: '#f472b6',
      dark: '#db2777',
    },
    success: {
      main: '#10b981',
      light: '#34d399',
      dark: '#059669',
    },
    warning: {
      main: '#f59e0b',
      light: '#fbbf24',
      dark: '#d97706',
    },
    error: {
      main: '#ef4444',
      light: '#f87171',
      dark: '#dc2626',
    },
    background: {
      default: '#fafbfc',
      paper: '#ffffff',
    },
    text: {
      primary: '#1f2937',
      secondary: '#6b7280',
    },
    grey: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      fontWeight: 500,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 1px 2px rgba(0, 0, 0, 0.05)',
    '0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)',
    '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
    '0px 10px 15px -3px rgba(0, 0, 0, 0.1), 0px 4px 6px -2px rgba(0, 0, 0, 0.05)',
    '0px 20px 25px -5px rgba(0, 0, 0, 0.1), 0px 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '0px 25px 50px -12px rgba(0, 0, 0, 0.25)',
    ...Array(18).fill('0px 25px 50px -12px rgba(0, 0, 0, 0.25)'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          padding: '10px 20px',
          fontSize: '0.875rem',
          fontWeight: 500,
          boxShadow: 'none',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
            transform: 'translateY(-1px)',
            boxShadow: '0px 4px 12px rgba(99, 102, 241, 0.4)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        outlined: {
          borderColor: '#e5e7eb',
          color: '#374151',
          '&:hover': {
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.04)',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid #f3f4f6',
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            boxShadow: '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: '#fafbfc',
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            '& fieldset': {
              borderColor: '#e5e7eb',
            },
            '&:hover fieldset': {
              borderColor: '#d1d5db',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#6366f1',
              borderWidth: 2,
            },
            '&.Mui-focused': {
              backgroundColor: '#ffffff',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500,
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          border: '1px solid #e5e7eb',
          color: '#6b7280',
          '&.Mui-selected': {
            backgroundColor: '#6366f1',
            color: '#ffffff',
            '&:hover': {
              backgroundColor: '#4f46e5',
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(99, 102, 241, 0.04)',
          },
        },
      },
    },
  },
});

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingOutput, setStreamingOutput] = useState('');
  const [testCases, setTestCases] = useState([]);
  const [excelUrl, setExcelUrl] = useState('');
  const [serverStatus, setServerStatus] = useState('checking');

  // 在组件加载时测试与后端的连接
  useEffect(() => {
    const checkServerConnection = async () => {
      try {
        const result = await pingServer();
        if (result.status === 'success') {
          setServerStatus('connected');
          console.log('与后端连接成功!');
        } else {
          setServerStatus('error');
          console.error('后端返回了意外的响应:', result);
        }
      } catch (error) {
        setServerStatus('error');
        console.error('无法连接到后端:', error);
        alert('无法连接到后端服务器\n请确保后端服务器正在运行并且可以访问。');
      }
    };

    checkServerConnection();
  }, []);

  const handleImageUpload = (file) => {
    setUploadedImage(file);
    // 重置之前的结果
    setStreamingOutput('');
    setTestCases([]);
    setExcelUrl('');
  };

  const handleGenerateTestCases = async (context, requirements, prdImages = [], prdText = null, feishuUrl = null) => {
    if ((!prdImages || prdImages.length === 0) && !prdText && !feishuUrl) {
      alert('请上传PRD图片、输入PRD文本或提供飞书文档链接');
      return;
    }
    setIsGenerating(true);
    setStreamingOutput('');
    setTestCases([]);
    try {
      const formData = new FormData();
      if (feishuUrl) {
        formData.append('feishu_url', feishuUrl);
      } else {
        if (prdImages && prdImages.length > 0) {
          prdImages.forEach((img) => {
            formData.append('images', img);
          });
        }
        if (prdText) {
          formData.append('prd_text', prdText);
        }
      }
      formData.append('context', context);
      formData.append('requirements', requirements);
      const response = await generateTestCases(formData);
      console.log('收到后端响应:', response.status);

      // 处理流式响应
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      console.log('开始读取流式响应...');

      // 读取流式响应
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('流式响应读取完成');
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // 更新流式输出
        setStreamingOutput(prev => prev + chunk);
        console.log('收到数据块:', chunk);
      }

      // 解析完整响应以获取测试用例
      console.log('开始解析测试用例...');
      console.log('完整的响应缓冲区:', buffer);

      // 尝试从注释中提取结构化的测试用例数据
      const testCasesJsonRegex = /<!-- TEST_CASES_JSON: (.+?) -->/;
      const testCasesMatch = buffer.match(testCasesJsonRegex);
      const parsedTestCases = [];

      if (testCasesMatch && testCasesMatch[1]) {
        console.log('找到结构化测试用例数据');

        try {
          const testCasesJson = JSON.parse(testCasesMatch[1]);
          console.log('解析的测试用例数据:', testCasesJson);

          if (Array.isArray(testCasesJson)) {
            // 处理测试用例数组
            for (const testCase of testCasesJson) {
              if (testCase.id && testCase.title && testCase.description && Array.isArray(testCase.steps)) {
                parsedTestCases.push(testCase);
              }
            }

            if (parsedTestCases.length > 0) {
              console.log('成功解析的测试用例数量:', parsedTestCases.length);
              setTestCases(parsedTestCases);
            }
          }
        } catch (jsonError) {
          console.error('解析结构化测试用例数据错误:', jsonError);
        }
      }

      // 如果没有找到结构化数据或解析失败，尝试其他方法
      if (parsedTestCases.length === 0) {
        // 尝试从注释中提取单个 JSON 数据
        const jsonDataRegex = /<!-- JSON_DATA: (.+?) -->/g;
        const matches = [...buffer.matchAll(jsonDataRegex)];

        if (matches.length > 0) {
          console.log('找到 JSON 数据注释:', matches.length);

          for (const match of matches) {
            try {
              const jsonStr = match[1];
              const testCase = JSON.parse(jsonStr);
              console.log('成功解析测试用例:', testCase);
              parsedTestCases.push(testCase);
            } catch (jsonError) {
              console.error('解析 JSON 数据错误:', jsonError);
            }
          }

          if (parsedTestCases.length > 0) {
            console.log('成功解析的测试用例数量:', parsedTestCases.length);
            setTestCases(parsedTestCases);
          }
        } else {
          // 如果没有找到 JSON 数据，尝试使用旧的方法解析
          console.log('没有找到 JSON 数据注释，尝试使用旧的方法解析');

          // 尝试将整个响应作为 Markdown 处理
          // 对于流式输出，我们可以直接使用缓冲区中的内容
          // 不需要额外解析 JSON

          // 如果有需要，仍然可以尝试解析 JSON
          const jsonStrings = buffer.split('\n').filter(str => str.trim() && str.startsWith('{') && str.endsWith('}'));

          if (jsonStrings.length > 0) {
            console.log('找到可能的 JSON 字符串:', jsonStrings.length);

            for (const jsonStr of jsonStrings) {
              try {
                const testCase = JSON.parse(jsonStr);
                console.log('成功解析测试用例:', testCase);
                parsedTestCases.push(testCase);
              } catch (jsonError) {
                console.error('解析 JSON 字符串错误:', jsonError);
              }
            }
          }

          if (parsedTestCases.length > 0) {
            console.log('成功解析的测试用例数量:', parsedTestCases.length);
            setTestCases(parsedTestCases);
          } else {
            console.warn('没有成功解析任何测试用例，但仍然有 Markdown 输出');
            // 创建一个空的测试用例数组，以便前端显示 Markdown 内容
            setTestCases([{
              id: 'TC-1',
              title: '测试用例',
              description: '请查看生成的 Markdown 内容',
              steps: [{ step_number: 1, description: '查看', expected_result: '生成的内容' }]
            }]);
          }
        }
      }
    } catch (error) {
      console.error('Error generating test cases:', error);
      console.error('Error details:', error.message);
      console.error('Error stack:', error.stack);
      setStreamingOutput(`生成测试用例时出错: ${error.message}\n请检查控制台以获取更多信息。`);
      alert(`请求错误: ${error.message}\n请检查浏览器控制台以获取更多信息。`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportToExcel = async () => {
    if (testCases.length === 0) {
      alert('No test cases to export');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/test-cases/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testCases),
      });

      if (response.ok) {
        // 从响应中获取blob
        const blob = await response.blob();

        // 为blob创建一个URL
        const url = window.URL.createObjectURL(blob);

        // 创建一个链接并点击它以下载文件
        const a = document.createElement('a');
        a.href = url;
        a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'test_cases.xlsx';
        document.body.appendChild(a);
        a.click();

        // 清理
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        console.error('Error exporting test cases:', await response.text());
        alert('Error exporting test cases. Please try again.');
      }
    } catch (error) {
      console.error('Error exporting test cases:', error);
      alert('Error exporting test cases. Please try again.');
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
        <Header serverStatus={serverStatus} />
        
        <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 }, px: { xs: 2, md: 3 } }}>
          {serverStatus === 'error' && (
            <Paper 
              elevation={0}
              sx={{ 
                mb: 3, 
                p: 3, 
                bgcolor: 'error.50', 
                borderRadius: 2, 
                border: '1px solid',
                borderColor: 'error.200',
                display: 'flex',
                alignItems: 'center',
                gap: 2
              }}
            >
              <Box sx={{ 
                width: 8, 
                height: 8, 
                borderRadius: '50%', 
                bgcolor: 'error.main',
                flexShrink: 0
              }} />
              <Typography variant="body2" color="error.dark" sx={{ fontWeight: 500 }}>
                无法连接到后端服务器，请确保服务器正在运行
              </Typography>
            </Paper>
          )}

          <Box sx={{ 
            display: 'flex', 
            gap: { xs: 2, md: 4 },
            flexDirection: { xs: 'column', lg: 'row' },
            alignItems: 'stretch'
          }}>
            {/* 左侧区域 - 输入区域 */}
            <Box sx={{ 
              width: { xs: '100%', lg: '42%' }, 
              minWidth: { lg: 420 },
              display: 'flex',
              flexDirection: 'column'
            }}>
              <UploadArea
                onImageUpload={handleImageUpload}
                onGenerateTestCases={handleGenerateTestCases}
                isGenerating={isGenerating}
                uploadedImage={uploadedImage}
                serverStatus={serverStatus}
              />
            </Box>

            {/* 右侧区域 - 输出 */}
            <Box sx={{ 
              width: { xs: '100%', lg: '58%' }, 
              display: 'flex', 
              flexDirection: 'column'
            }}>
              <Paper 
                elevation={0}
                sx={{ 
                  p: { xs: 3, md: 4 }, 
                  flexGrow: 1,
                  minHeight: { xs: 400, md: 600 },
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center', 
                  mb: 3,
                  flexWrap: 'wrap',
                  gap: 2
                }}>
                  <Box>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {isGenerating ? '正在生成测试用例' : '测试用例结果'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {isGenerating ? '请稍候，AI正在分析并生成测试用例...' : 
                       testCases.length > 0 ? `已生成 ${testCases.length} 个测试用例` : 
                       '上传图片或输入PRD文本开始生成'}
                    </Typography>
                  </Box>
                  {!isGenerating && testCases.length > 0 && (
                    <Button
                      variant="outlined"
                      startIcon={<FileDownloadIcon />}
                      onClick={handleExportToExcel}
                      sx={{ flexShrink: 0 }}
                    >
                      导出Excel
                    </Button>
                  )}
                </Box>

                <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  {isGenerating ? (
                    <StreamingOutput content={streamingOutput} />
                  ) : testCases.length > 0 ? (
                    <TestCaseDisplay
                      testCases={testCases}
                      onExportToExcel={handleExportToExcel}
                    />
                  ) : (
                    <Box sx={{ 
                      flexGrow: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      textAlign: 'center',
                      py: 6
                    }}>
                      <Box sx={{ 
                        width: 80, 
                        height: 80, 
                        borderRadius: '50%', 
                        bgcolor: 'grey.100',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mb: 3
                      }}>
                        <AutoAwesomeIcon sx={{ fontSize: 40, color: 'grey.400' }} />
                      </Box>
                      <Typography variant="h6" sx={{ mb: 1, fontWeight: 500 }}>
                        开始生成测试用例
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }}>
                        选择图片上传或输入PRD文本，填写相关信息后点击生成按钮
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Paper>
            </Box>
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
