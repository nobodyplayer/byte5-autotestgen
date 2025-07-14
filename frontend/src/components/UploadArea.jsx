import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ImageIcon from '@mui/icons-material/Image';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import ArticleIcon from '@mui/icons-material/Article';
import LinkIcon from '@mui/icons-material/Link';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import ClearIcon from '@mui/icons-material/Clear';
import InfoIcon from '@mui/icons-material/Info';
import { useDropzone } from 'react-dropzone';
import Grid from '@mui/material/Grid';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

const UploadArea = ({ onImageUpload, onGenerateTestCases, isGenerating, uploadedImage, serverStatus = 'checking' }) => {
  // 删除 context 相关状态
  const [humanReferenceCases, setHumanReferenceCases] = useState('');
  const [inputType, setInputType] = useState('prd'); // 'prd' 或 'feishu'
  const [prdText, setPrdText] = useState('');
  const [feishuUrl, setFeishuUrl] = useState('');
  const [prdImages, setPrdImages] = useState([]); // 存储PRD相关的图片
  const [humanCasesInputMode, setHumanCasesInputMode] = useState('text'); // 'text' or 'csv'
  const [humanCasesCsvFile, setHumanCasesCsvFile] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      if (inputType === 'prd') {
        // PRD模式下支持多图片上传
        setPrdImages(prev => [...prev, ...acceptedFiles]);
      } else {
        // 保持原有的单图片上传逻辑（如果需要的话）
        onImageUpload(acceptedFiles[0]);
      }
    }
  }, [onImageUpload, inputType]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    },
    maxFiles: inputType === 'prd' ? 10 : 1, // PRD模式支持最多10张图片
    multiple: inputType === 'prd'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputType === 'prd') {
      onGenerateTestCases('', humanReferenceCases, prdImages, prdText, null, humanCasesCsvFile);
    } else if (inputType === 'feishu') {
      onGenerateTestCases('', humanReferenceCases, null, null, feishuUrl, humanCasesCsvFile);
    }
  };

  const handleHumanCasesCsvUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setHumanCasesCsvFile(file);
      } else {
        alert('请上传CSV格式的文件');
        setHumanCasesCsvFile(null);
      }
    }
  };

  const handleRemoveHumanCasesCsv = () => {
    setHumanCasesCsvFile(null);
    const fileInput = document.getElementById('human-cases-csv-input');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const handleInputTypeChange = (event, newInputType) => {
    if (newInputType !== null) {
      setInputType(newInputType);
    }
  };

  return (
    <Paper 
      elevation={0}
      sx={{ 
        p: { xs: 3, md: 4 }, 
        height: 'fit-content',
        position: 'sticky',
        top: 24
      }}
    >
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          测试用例生成器
        </Typography>

      </Box>
      
      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                选择输入方式
              </Typography>
              <ToggleButtonGroup
                value={inputType}
                exclusive
                onChange={handleInputTypeChange}
                size="medium"
                sx={{ width: '100%' }}
              >
                <ToggleButton 
                  value="prd" 
                  sx={{ 
                    flex: 1, 
                    py: 1.5,
                    flexDirection: 'column',
                    gap: 1
                  }}
                >
                  <ArticleIcon />
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    PRD文档
                  </Typography>
                </ToggleButton>
                <ToggleButton 
                  value="feishu"
                  sx={{ 
                    flex: 1, 
                    py: 1.5,
                    flexDirection: 'column',
                    gap: 1
                  }}
                >
                  <LinkIcon />
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    飞书文档
                  </Typography>
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>
          </Grid>

          {inputType === 'prd' && (
          <Grid item xs={12}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                输入PRD文档
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={10}
                variant="outlined"
                label="产品需求文档内容"
                placeholder="请详细描述产品功能、用户故事、业务流程、交互逻辑等内容...\n\n示例：\n1. 用户登录功能\n- 用户可以通过手机号和密码登录\n- 支持短信验证码登录\n- 登录失败3次后账号锁定30分钟\n\n2. 商品搜索功能\n- 用户可以通过关键词搜索商品\n- 支持按分类、价格、品牌筛选\n- 搜索结果按相关度排序"
                value={prdText}
                onChange={(e) => setPrdText(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    bgcolor: 'grey.50',
                    '&:hover': {
                      bgcolor: 'white',
                    },
                    '&.Mui-focused': {
                      bgcolor: 'white',
                    }
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                建议输入详细的功能描述，包含用户操作流程和预期结果，以获得更准确的测试用例
              </Typography>
              
              <Box sx={{ mt: 4 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                  上传PRD相关图片（可选）
                </Typography>
                <Box
                  {...getRootProps()}
                  sx={{
                    border: '2px dashed',
                    borderColor: isDragActive ? 'primary.main' : 'grey.300',
                    borderRadius: 3,
                    p: 4,
                    textAlign: 'center',
                    cursor: 'pointer',
                    bgcolor: isDragActive ? 'primary.50' : 'grey.50',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: 'primary.50',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <input {...getInputProps()} />
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center',
                    gap: 2
                  }}>
                    <Box sx={{
                      width: 64,
                      height: 64,
                      borderRadius: '50%',
                      bgcolor: 'primary.100',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <CloudUploadIcon sx={{ fontSize: 32, color: 'primary.main' }} />
                    </Box>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {isDragActive ? '放开以上传文件' : '拖拽图片到这里'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        或者 <Box component="span" sx={{ color: 'primary.main', fontWeight: 500 }}>点击浏览</Box> 选择文件
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        支持 JPG、PNG、GIF 格式，可上传多张图片，每张最大 10MB
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                {prdImages.length > 0 && (
                  <Paper 
                    elevation={0}
                    sx={{ 
                      mt: 3, 
                      p: 3, 
                      border: '1px solid', 
                      borderColor: 'success.200',
                      borderRadius: 2,
                      bgcolor: 'success.50'
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                      已上传 {prdImages.length} 张图片
                    </Typography>
                    <Grid container spacing={2}>
                      {prdImages.map((img, index) => (
                        <Grid item xs={12} sm={6} md={4} key={index}>
                          <Box sx={{ 
                            position: 'relative',
                            borderRadius: 2, 
                            overflow: 'hidden',
                            bgcolor: 'white',
                            border: '1px solid',
                            borderColor: 'grey.200',
                            height: '150px'
                          }}>
                            <img
                              src={URL.createObjectURL(img)}
                              alt={`上传的图片 ${index + 1}`}
                              style={{ 
                                width: '100%', 
                                height: '100%', 
                                objectFit: 'contain',
                                display: 'block'
                              }}
                            />
                            <Button
                              variant="contained"
                              color="error"
                              size="small"
                              sx={{ 
                                position: 'absolute', 
                                top: 5, 
                                right: 5,
                                minWidth: 'auto',
                                width: 32,
                                height: 32,
                                borderRadius: '50%'
                              }}
                              onClick={(e) => {
                                e.stopPropagation();
                                setPrdImages(prev => prev.filter((_, i) => i !== index));
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </Button>
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                position: 'absolute',
                                bottom: 0,
                                left: 0,
                                right: 0,
                                bgcolor: 'rgba(0,0,0,0.6)',
                                color: 'white',
                                p: 0.5,
                                textAlign: 'center',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {img.name} ({(img.size / 1024 / 1024).toFixed(2)} MB)
                            </Typography>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button 
                        variant="outlined" 
                        color="error" 
                        startIcon={<DeleteIcon />}
                        onClick={() => setPrdImages([])}
                      >
                        清空所有图片
                      </Button>
                    </Box>
                  </Paper>
                )}
              </Box>
            </Box>
          </Grid>
          )}

          {inputType === 'feishu' && (
          <Grid item xs={12}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                飞书文档链接
              </Typography>
              <TextField
                fullWidth
                variant="outlined"
                label="飞书文档URL"
                placeholder="请输入飞书文档链接，例如：https://sample.feishu.cn/docx/UXEAd6cRUoj5pexJZr0cdwaFnpd"
                value={feishuUrl}
                onChange={(e) => setFeishuUrl(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    bgcolor: 'grey.50',
                    '&:hover': {
                      bgcolor: 'white',
                    },
                    '&.Mui-focused': {
                      bgcolor: 'white',
                    }
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                支持新版文档（docx）和旧版文档（doc），请确保文档具有访问权限
              </Typography>
            </Box>
          </Grid>
          )}

          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 3 }}>
                人工参考用例配置
              </Typography>
              <Stack spacing={3}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>选择输入方式</InputLabel>
                  <Select
                    value={humanCasesInputMode}
                    onChange={(e) => setHumanCasesInputMode(e.target.value)}
                    label="选择输入方式"
                    sx={{
                      borderRadius: 2,
                      bgcolor: 'grey.50',
                      '&:hover': {
                        bgcolor: 'white',
                      },
                      '&.Mui-focused': {
                        bgcolor: 'white',
                      }
                    }}
                  >
                    <MenuItem value="text">直接文本输入</MenuItem>
                    <MenuItem value="csv">CSV文件上传</MenuItem>
                  </Select>
                </FormControl>

                {humanCasesInputMode === 'text' ? (
                  <TextField
                    label="人工参考用例（可选）"
                    multiline
                    rows={6}
                    fullWidth
                    value={humanReferenceCases}
                    onChange={(e) => setHumanReferenceCases(e.target.value)}
                    placeholder="请输入人工编写的参考测试用例，AI将参考这些用例生成更准确的测试点...\n\n例如：\n• 用户登录测试：输入正确用户名密码，验证登录成功\n• 密码错误测试：输入错误密码，验证提示错误信息\n• 商品搜索测试：输入关键词，验证搜索结果准确性\n• 订单支付测试：选择商品下单，验证支付流程完整性"
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        bgcolor: 'grey.50',
                        '&:hover': {
                          bgcolor: 'white',
                        },
                        '&.Mui-focused': {
                          bgcolor: 'white',
                        }
                      }
                    }}
                  />
                ) : (
                  <Box>
                    <input
                      id="human-cases-csv-input"
                      type="file"
                      accept=".csv"
                      onChange={handleHumanCasesCsvUpload}
                      style={{ display: 'none' }}
                    />
                    <label htmlFor="human-cases-csv-input">
                      <Button
                        variant="outlined"
                        component="span"
                        startIcon={<FileUploadIcon />}
                        fullWidth
                        sx={{ 
                          mb: 2, 
                          py: 2,
                          borderRadius: 2,
                          bgcolor: 'grey.50',
                          '&:hover': {
                            bgcolor: 'white',
                          }
                        }}
                      >
                        选择人工用例CSV文件（可选）
                      </Button>
                    </label>
                    {humanCasesCsvFile && (
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 1, 
                        p: 2, 
                        bgcolor: 'success.50', 
                        borderRadius: 2,
                        border: '1px solid',
                        borderColor: 'success.200',
                        mb: 2
                      }}>
                        <CloudUploadIcon sx={{ color: 'success.main' }} />
                        <Typography variant="body2" sx={{ flexGrow: 1 }}>
                          {humanCasesCsvFile.name}
                        </Typography>
                        <IconButton size="small" onClick={handleRemoveHumanCasesCsv}>
                          <ClearIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    )}
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
                      <InfoIcon fontSize="small" />
                      CSV文件应包含人工参考用例，每行一个用例
                    </Typography>
                  </Box>
                )}
              </Stack>
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={
                isGenerating || 
                serverStatus !== 'connected' ||
                (inputType === 'prd' && !prdText.trim() && prdImages.length === 0) ||
                (inputType === 'feishu' && !feishuUrl.trim())
              }
              sx={{
                py: 2,
                fontSize: '1.1rem',
                fontWeight: 600,
                borderRadius: 2,
                textTransform: 'none',
                boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                '&:hover': {
                  boxShadow: '0 6px 16px rgba(25, 118, 210, 0.4)',
                  transform: 'translateY(-1px)',
                },
                '&:disabled': {
                  bgcolor: 'grey.300',
                  color: 'grey.500',
                  boxShadow: 'none',
                },
                transition: 'all 0.2s ease'
              }}
            >
              {isGenerating ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={20} color="inherit" />
                  <Typography variant="inherit">AI正在生成功能测试点...</Typography>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <UploadFileIcon />
                  <Typography variant="inherit">开始生成功能测试点</Typography>
                </Box>
              )}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default UploadArea;
