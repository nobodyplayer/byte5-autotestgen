import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Chip,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Assessment as AssessmentIcon,
  FileUpload as FileUploadIcon,
  Clear as ClearIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { evaluateTestCases } from '../services/api';
import StreamingOutput from './StreamingOutput';

const AutoEvaluation = () => {
  const [aiGeneratedCases, setAiGeneratedCases] = useState('');
  const [humanReferenceCases, setHumanReferenceCases] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [inputMode, setInputMode] = useState('text'); // 'text' or 'csv'
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState('');
  const [error, setError] = useState('');

  const handleCsvFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setCsvFile(file);
        setError('');
      } else {
        setError('请上传CSV格式的文件');
        setCsvFile(null);
      }
    }
  };

  const handleRemoveCsvFile = () => {
    setCsvFile(null);
    const fileInput = document.getElementById('csv-file-input');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const [aiInputMode, setAiInputMode] = useState('text'); // 新增AI用例输入模式
  const [aiCsvFile, setAiCsvFile] = useState(null); // 新增AI用例CSV文件

  const handleEvaluate = async () => {
    if (aiInputMode === 'text' && !aiGeneratedCases.trim()) {
      setError('请输入AI生成的测试用例');
      return;
    }
    if (aiInputMode === 'csv' && !aiCsvFile) {
      setError('请上传AI用例的CSV文件');
      return;
    }
    if (inputMode === 'text' && !humanReferenceCases.trim()) {
      setError('请输入人工参考用例');
      return;
    }
    if (inputMode === 'csv' && !csvFile) {
      setError('请上传包含人工用例的CSV文件');
      return;
    }
    setIsEvaluating(true);
    setEvaluationResult('');
    setError('');
    try {
      const formData = new FormData();
      if (aiInputMode === 'text') {
        formData.append('ai_generated_cases', aiGeneratedCases);
      } else {
        formData.append('ai_csv_file', aiCsvFile);
      }
      if (inputMode === 'text') {
        formData.append('human_reference_cases', humanReferenceCases);
      } else {
        formData.append('csv_file', csvFile);
      }
      const response = await evaluateTestCases(formData);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        setEvaluationResult(buffer);
      }
    } catch (error) {
      console.error('评测过程中发生错误:', error);
      setError('评测过程中发生错误，请重试');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleClear = () => {
    setAiGeneratedCases('');
    setHumanReferenceCases('');
    setCsvFile(null);
    setAiCsvFile(null);
    setEvaluationResult('');
    setError('');
    const fileInput = document.getElementById('csv-file-input');
    if (fileInput) fileInput.value = '';
    const aiFileInput = document.getElementById('ai-csv-file-input');
    if (aiFileInput) aiFileInput.value = '';
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Paper elevation={0} sx={{ p: 4, borderRadius: 2 }}>
        {/* 标题区域 */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <AssessmentIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h4" sx={{ fontWeight: 600 }}>
              自动化评测
            </Typography>
          </Box>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            将AI生成的测试用例与人工编写的参考用例进行对比评测，从覆盖度、深度、一致性、可执行性和简洁性五个维度进行评估。
          </Typography>
          <Alert severity="info" sx={{ borderRadius: 2 }}>
            <Typography variant="body2">
              <strong>评测维度：</strong>核心功能覆盖度、测试深度与广度、语义一致性、表达质量与可执行性、简洁性与无冗余
            </Typography>
          </Alert>
        </Box>

        <Grid container spacing={4}>
          {/* 左侧输入区域 */}
          <Grid item xs={12} lg={6}>
            <Card elevation={0} sx={{ border: '1px solid', borderColor: 'grey.200', borderRadius: 2 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  输入测试用例
                </Typography>

                {/* AI生成用例输入 */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500 }}>
                    AI生成的测试用例 *
                  </Typography>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>选择输入方式</InputLabel>
                    <Select
                      value={aiInputMode}
                      onChange={(e) => setAiInputMode(e.target.value)}
                      label="选择输入方式"
                    >
                      <MenuItem value="text">直接文本输入</MenuItem>
                      <MenuItem value="csv">CSV文件上传</MenuItem>
                    </Select>
                  </FormControl>
                  {aiInputMode === 'text' ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={6}
                      value={aiGeneratedCases}
                      onChange={(e) => setAiGeneratedCases(e.target.value)}
                      placeholder="请输入AI生成的测试用例，每行一个用例...\n例如：\n检查用户使用正确密码是否能登录\n错误登录是否提示\n多次输错密码是否有风控机制"
                      variant="outlined"
                      sx={{ mb: 2 }}
                    />
                  ) : (
                    <Box>
                      <input
                        id="ai-csv-file-input"
                        type="file"
                        accept=".csv"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
                            setAiCsvFile(file);
                            setError('');
                          } else {
                            setError('请上传AI用例的CSV格式文件');
                            setAiCsvFile(null);
                          }
                        }}
                        style={{ display: 'none' }}
                      />
                      <label htmlFor="ai-csv-file-input">
                        <Button
                          variant="outlined"
                          component="span"
                          startIcon={<FileUploadIcon />}
                          fullWidth
                          sx={{ mb: 2, py: 2 }}
                        >
                          选择AI用例CSV文件
                        </Button>
                      </label>
                      {aiCsvFile && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2, bgcolor: 'grey.50', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                          <CloudUploadIcon sx={{ color: 'success.main' }} />
                          <Typography variant="body2" sx={{ flexGrow: 1 }}>{aiCsvFile.name}</Typography>
                          <IconButton size="small" onClick={() => { setAiCsvFile(null); document.getElementById('ai-csv-file-input').value = ''; }}>
                            <ClearIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      )}
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
                        <InfoIcon fontSize="small" />
                        CSV文件应包含AI生成的测试用例，每行一个用例
                      </Typography>
                    </Box>
                  )}
                </Box>

                <Divider sx={{ my: 3 }} />

                {/* 人工参考用例输入模式选择 */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 500 }}>
                    人工参考用例输入方式 *
                  </Typography>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>选择输入方式</InputLabel>
                    <Select
                      value={inputMode}
                      onChange={(e) => setInputMode(e.target.value)}
                      label="选择输入方式"
                    >
                      <MenuItem value="text">直接文本输入</MenuItem>
                      <MenuItem value="csv">CSV文件上传</MenuItem>
                    </Select>
                  </FormControl>

                  {inputMode === 'text' ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={6}
                      value={humanReferenceCases}
                      onChange={(e) => setHumanReferenceCases(e.target.value)}
                      placeholder="请输入人工编写的参考测试用例，每行一个用例...\n例如：\n验证用户可以使用正确账号密码登录\n验证错误密码时系统提示信息正确\n验证登录失败三次后账号是否被锁定"
                      variant="outlined"
                    />
                  ) : (
                    <Box>
                      <input
                        id="csv-file-input"
                        type="file"
                        accept=".csv"
                        onChange={handleCsvFileUpload}
                        style={{ display: 'none' }}
                      />
                      <label htmlFor="csv-file-input">
                        <Button
                          variant="outlined"
                          component="span"
                          startIcon={<FileUploadIcon />}
                          fullWidth
                          sx={{ mb: 2, py: 2 }}
                        >
                          选择CSV文件
                        </Button>
                      </label>
                      {csvFile && (
                        <Box sx={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: 1, 
                          p: 2, 
                          bgcolor: 'grey.50', 
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'grey.200'
                        }}>
                          <CloudUploadIcon sx={{ color: 'success.main' }} />
                          <Typography variant="body2" sx={{ flexGrow: 1 }}>
                            {csvFile.name}
                          </Typography>
                          <IconButton size="small" onClick={handleRemoveCsvFile}>
                            <ClearIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      )}
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
                        <InfoIcon fontSize="small" />
                        CSV文件应包含测试用例，每行一个用例
                      </Typography>
                    </Box>
                  )}
                </Box>

                {/* 操作按钮 */}
                <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
                  <Button
                    variant="contained"
                    onClick={handleEvaluate}
                    disabled={isEvaluating}
                    startIcon={isEvaluating ? <CircularProgress size={20} /> : <AssessmentIcon />}
                    sx={{ flexGrow: 1 }}
                  >
                    {isEvaluating ? '评测中...' : '开始评测'}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={handleClear}
                    disabled={isEvaluating}
                  >
                    清空
                  </Button>
                </Box>

                {error && (
                  <Alert severity="error" sx={{ mt: 2, borderRadius: 2 }}>
                    {error}
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* 右侧结果区域 */}
          <Grid item xs={12} lg={6}>
            <Card elevation={0} sx={{ border: '1px solid', borderColor: 'grey.200', borderRadius: 2, height: '100%' }}>
              <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  评测结果
                </Typography>

                <Box sx={{ flexGrow: 1, minHeight: 400 }}>
                  {isEvaluating || evaluationResult ? (
                    <StreamingOutput content={evaluationResult} />
                  ) : (
                    <Box sx={{ 
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      textAlign: 'center',
                      color: 'text.secondary'
                    }}>
                      <AssessmentIcon sx={{ fontSize: 64, mb: 2, color: 'grey.300' }} />
                      <Typography variant="h6" sx={{ mb: 1 }}>
                        等待评测
                      </Typography>
                      <Typography variant="body2">
                        输入测试用例后点击"开始评测"查看结果
                      </Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default AutoEvaluation;