import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import InfoIcon from '@mui/icons-material/Info';
import CloseIcon from '@mui/icons-material/Close';
import { generateMindMap } from '../services/api';

const MindMapDisplay = ({ testPoints }) => {
  const svgRef = useRef();
  const [mindMapData, setMindMapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [selectedNode, setSelectedNode] = useState(null);
  const [detailDialog, setDetailDialog] = useState(false);

  // 切换节点展开/收起状态
  const toggleNode = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // 处理节点点击事件
  const handleNodeClick = (node) => {
    // 只有测试用例节点（有steps属性）才能点击查看详情
    if (node.steps && node.steps.length > 0) {
      setSelectedNode(node);
      setDetailDialog(true);
    }
  };

  // 关闭详情对话框
  const handleCloseDetailDialog = () => {
    setDetailDialog(false);
    setSelectedNode(null);
  };

  // 将测试点数据转换为思维导图所需的格式
  const convertTestPointsToTestCases = (testPoints) => {
    const testCases = [];
    
    if (testPoints && testPoints.modules) {
      testPoints.modules.forEach((module, moduleIndex) => {
        if (module.points && Array.isArray(module.points)) {
          module.points.forEach((point, pointIndex) => {
            const testCase = {
              id: `TC-${moduleIndex + 1}-${pointIndex + 1}`,
              title: point.title || point.name || `测试点 ${pointIndex + 1}`,
              description: point.description || point.desc || '',
              priority: point.priority || 'Medium',
              preconditions: point.preconditions || '',
              steps: point.steps || [
                {
                  step_number: 1,
                  description: point.description || point.desc || '执行测试',
                  expected_result: point.expected || '符合预期结果'
                }
              ]
            };
            testCases.push(testCase);
          });
        }
      });
    }
    
    return testCases;
  };

  // 生成思维导图
  const handleGenerateMindMap = async () => {
    if (!testPoints) {
      setError('没有可用的测试点数据');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 检查是否已经是新的数据格式（有children属性）
      let mindMapStructure;
      if (testPoints.children) {
        // 已经是新格式，直接使用
        mindMapStructure = testPoints;
      } else {
        // 旧格式，需要转换
        const testCases = convertTestPointsToTestCases(testPoints);
        console.log('转换后的测试用例:', testCases);
        
        if (testCases.length === 0) {
          setError('没有找到有效的测试用例数据');
          setLoading(false);
          return;
        }

        const response = await generateMindMap(testCases);
        mindMapStructure = response.mindmap;
      }
      
      setMindMapData(mindMapStructure);
      
      // 默认展开根节点和第一层节点
      const newExpanded = new Set();
      if (mindMapStructure && mindMapStructure.name) {
        const rootNodeId = `node-0-${mindMapStructure.name.replace(/\s+/g, '-')}`;
        newExpanded.add(rootNodeId);
        
        // 展开第一层子节点（模块节点）
        if (mindMapStructure.children) {
          mindMapStructure.children.forEach((child, index) => {
            const moduleNodeId = `node-1-${child.name.replace(/\s+/g, '-')}`;
            newExpanded.add(moduleNodeId);
          });
        }
      }
      setExpandedNodes(newExpanded);
      
      setLoading(false);
    } catch (err) {
      console.error('生成思维导图失败:', err);
      setError('生成思维导图失败: ' + (err.message || '未知错误'));
      setLoading(false);
    }
  };

  // 获取节点样式
  const getNodeStyle = (level) => {
    const styles = [
      { color: '#1976d2', fontSize: '18px', fontWeight: 'bold' }, // 根节点
      { color: '#2e7d32', fontSize: '16px', fontWeight: '600' },  // 一级节点
      { color: '#f57c00', fontSize: '14px', fontWeight: '500' },  // 二级节点
      { color: '#c2185b', fontSize: '13px', fontWeight: 'normal' }, // 三级节点
      { color: '#7b1fa2', fontSize: '12px', fontWeight: 'normal' }  // 四级节点
    ];
    return styles[Math.min(level, styles.length - 1)];
  };

  // 获取节点主题
  const getNodeTheme = (level) => {
    const themes = [
      { bg: '#e3f2fd', border: '#1976d2', text: '#0d47a1' }, // 根节点
      { bg: '#e8f5e8', border: '#2e7d32', text: '#1b5e20' }, // 一级节点
      { bg: '#fff3e0', border: '#f57c00', text: '#e65100' }, // 二级节点
      { bg: '#fce4ec', border: '#c2185b', text: '#880e4f' }, // 三级节点
      { bg: '#f3e5f5', border: '#7b1fa2', text: '#4a148c' }  // 四级节点
    ];
    return themes[Math.min(level, themes.length - 1)];
  };

  // 渲染连接线
  const renderConnector = (level) => {
    if (level === 0) return null;
    
    return (
      <Box
        sx={{
          position: 'absolute',
          left: -20,
          top: '50%',
          width: 20,
          height: 2,
          backgroundColor: '#666',
          transform: 'translateY(-50%)',
        }}
      />
    );
  };





  // 切换节点展开状态
  const toggleNodeExpansion = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // 渲染思维导图节点
  const renderMindMapNode = (node, level = 0, isLast = false) => {
    const theme = getNodeTheme(level);
    const marginLeft = level * 50;
    const nodeId = `node-${level}-${node.name.replace(/\s+/g, '-')}`;
    const isExpanded = expandedNodes.has(nodeId) || level === 0; // 根节点默认展开
    const hasChildren = node.children && node.children.length > 0;
    const isTestCase = node.steps && node.steps.length > 0;
    
    return (
      <Box 
        key={nodeId} 
        sx={{ 
          position: 'relative', 
          mb: 2,
          opacity: 0,
          animation: 'fadeInUp 0.6s ease forwards',
          animationDelay: `${level * 0.1}s`,
          '@keyframes fadeInUp': {
            '0%': {
              opacity: 0,
              transform: 'translateY(20px)'
            },
            '100%': {
              opacity: 1,
              transform: 'translateY(0)'
            }
          }
        }}
      >
        <Box sx={{ ml: `${marginLeft}px`, position: 'relative' }}>
          {renderConnector(level)}
          
          <Card
            elevation={level === 0 ? 6 : 3}
            onClick={() => {
              if (hasChildren) {
                toggleNodeExpansion(nodeId);
              } else if (isTestCase) {
                handleNodeClick(node);
              }
            }}
            sx={{
              minWidth: 220,
              maxWidth: 450,
              border: `3px solid ${theme.border}`,
              backgroundColor: theme.bg,
              transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
              cursor: hasChildren || isTestCase ? 'pointer' : 'default',
              position: 'relative',
              overflow: 'visible',
              '&:hover': {
                transform: hasChildren || isTestCase ? 'translateY(-4px) scale(1.02)' : 'translateY(-2px)',
                boxShadow: `0 8px 25px ${theme.border}60`,
                borderColor: theme.border,
                backgroundColor: isTestCase ? '#e3f2fd' : theme.bg,
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: '-3px',
                  left: '-3px',
                  right: '-3px',
                  bottom: '-3px',
                  background: `linear-gradient(45deg, ${theme.border}40, transparent)`,
                  borderRadius: '12px',
                  zIndex: -1
                }
              }
            }}
          >
            <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography
                  variant={level === 0 ? 'h5' : level === 1 ? 'h6' : 'subtitle1'}
                  sx={{
                    fontWeight: level === 0 ? 'bold' : level === 1 ? '600' : '500',
                    color: theme.text,
                    flex: 1,
                    textShadow: level === 0 ? '0 1px 2px rgba(0,0,0,0.1)' : 'none'
                  }}
                >
                  {level === 0 && '🎯 '}
                  {level === 1 && '📦 '}
                  {level === 2 && '⚙️ '}
                  {level >= 3 && '🔍 '}
                  {node.name}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {isTestCase && (
                    <Tooltip title="点击查看详细步骤">
                      <InfoIcon color="primary" fontSize="small" />
                    </Tooltip>
                  )}
                  
                  {level > 0 && (
                    <Chip
                      label={`L${level}`}
                      size="small"
                      sx={{
                        backgroundColor: theme.border,
                        color: 'white',
                        fontSize: '10px',
                        height: '22px',
                        fontWeight: 'bold'
                      }}
                    />
                  )}
                  
                  {hasChildren && (
                    <Chip
                      label={isExpanded ? '▼' : '▶'}
                      size="small"
                      sx={{
                        backgroundColor: 'transparent',
                        color: theme.border,
                        fontSize: '12px',
                        height: '22px',
                        border: `1px solid ${theme.border}`,
                        transition: 'transform 0.3s ease',
                        transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)'
                      }}
                    />
                  )}
                  
                  {isTestCase && node.priority && (
                    <Chip
                      size="small"
                      label={node.priority}
                      color={node.priority === 'High' ? 'error' : node.priority === 'Medium' ? 'warning' : 'success'}
                      variant="outlined"
                    />
                  )}
                  
                  {isTestCase && node.status && (
                    <Chip
                      size="small"
                      label={node.status === 'passed' ? '通过' : node.status === 'failed' ? '不通过' : '待确认'}
                      color={node.status === 'passed' ? 'success' : node.status === 'failed' ? 'error' : 'default'}
                      variant="filled"
                    />
                  )}
                </Box>
              </Box>
              
              {node.description && (
                <Typography
                  variant="body2"
                  sx={{
                    color: '#666',
                    fontSize: '13px',
                    fontStyle: 'italic',
                    mb: 1,
                    lineHeight: 1.4
                  }}
                >
                  {node.description}
                </Typography>
              )}
              
              {hasChildren && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  <Chip
                    label={`${node.children.length} 个子项`}
                    size="small"
                    variant="outlined"
                    sx={{
                      borderColor: theme.border,
                      color: theme.text,
                      fontSize: '11px',
                      height: '24px',
                      fontWeight: '500'
                    }}
                  />
                  
                  {!isExpanded && (
                    <Typography variant="caption" sx={{ color: '#999', fontSize: '10px' }}>
                      点击展开
                    </Typography>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
        
        {hasChildren && isExpanded && (
          <Box
            sx={{
              overflow: 'hidden',
              transition: 'all 0.5s ease',
              opacity: isExpanded ? 1 : 0,
              maxHeight: isExpanded ? '2000px' : '0px'
            }}
          >
            {node.children.map((child, index) => 
              renderMindMapNode(child, level + 1, index === node.children.length - 1)
            )}
          </Box>
        )}
      </Box>
    );
  };

  // 渲染测试用例详情对话框
  const renderTestCaseDetailDialog = () => {
    if (!selectedNode || !detailDialog) return null;

    return (
      <Dialog
        open={detailDialog}
        onClose={handleCloseDetailDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            🔍 {selectedNode.title || selectedNode.name}
          </Typography>
          <IconButton onClick={handleCloseDetailDialog}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent>
          {selectedNode.description && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                描述
              </Typography>
              <Typography variant="body2" sx={{ color: '#666' }}>
                {selectedNode.description}
              </Typography>
            </Box>
          )}
          
          {selectedNode.preconditions && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                前置条件
              </Typography>
              <Typography variant="body2" sx={{ color: '#666' }}>
                {selectedNode.preconditions}
              </Typography>
            </Box>
          )}
          
          <Typography variant="subtitle2" color="primary" gutterBottom>
            测试步骤
          </Typography>
          
          <List>
            {selectedNode.steps && selectedNode.steps.map((step, index) => (
              <Box key={index}>
                <ListItem sx={{ px: 0 }}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                        <Chip
                          label={step.step_number || index + 1}
                          size="small"
                          color="primary"
                          sx={{ minWidth: '32px', fontSize: '12px' }}
                        />
                        <Typography variant="body2" sx={{ flex: 1 }}>
                          {step.description}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      step.expected_result && (
                        <Box sx={{ mt: 1, ml: 5 }}>
                          <Typography variant="caption" color="success.main" sx={{ fontWeight: 'bold' }}>
                            预期结果：
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {step.expected_result}
                          </Typography>
                        </Box>
                      )
                    }
                  />
                </ListItem>
                {index < selectedNode.steps.length - 1 && <Divider />}
              </Box>
            ))}
          </List>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleCloseDetailDialog} color="primary">
            关闭
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  // 渲染简化的测试点视图（当没有生成思维导图时）
  const renderSimpleTestPoints = () => {
    if (!testPoints || !testPoints.modules) return null;
    
    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="h6" sx={{ mb: 2, color: '#1976d2', fontWeight: 'bold' }}>
          📋 测试点预览
        </Typography>
        
        {testPoints.modules.map((module, moduleIndex) => (
          <Card key={moduleIndex} sx={{ mb: 2, border: '1px solid #e0e0e0' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#1976d2', mb: 1 }}>
                {module.name}
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {module.points && module.points.map((point, pointIndex) => (
                  <Chip
                    key={pointIndex}
                    label={point.title || point.name || `测试点 ${pointIndex + 1}`}
                    variant="outlined"
                    size="small"
                    sx={{
                      borderColor: '#2e7d32',
                      color: '#2e7d32',
                      '&:hover': {
                        backgroundColor: '#e8f5e8'
                      }
                    }}
                  />
                ))}
              </Box>
              
              {module.points && (
                <Typography variant="caption" sx={{ color: '#666', mt: 1, display: 'block' }}>
                  共 {module.points.length} 个测试点
                </Typography>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  };

  return (
    <Paper
      elevation={1}
      sx={{
        p: 2,
        backgroundColor: '#fafafa',
        borderRadius: 1,
        border: '1px solid #e0e0e0'
      }}
    >
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 2
      }}>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 'bold',
            color: '#333'
          }}
        >
          测试用例思维导图
        </Typography>
        
        <Button
          variant="contained"
          onClick={handleGenerateMindMap}
          disabled={loading || !testPoints}
          sx={{
            backgroundColor: '#1976d2',
            '&:hover': {
              backgroundColor: '#1565c0'
            }
          }}
        >
          {loading ? (
            <>
              <CircularProgress size={18} sx={{ mr: 1, color: 'white' }} />
              生成中...
            </>
          ) : (
            '生成思维导图'
          )}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!mindMapData && !loading && (
        <Box>
          <Box sx={{ textAlign: 'center', py: 2, color: '#666', mb: 2 }}>
            <Typography variant="body1">
              点击"生成思维导图"按钮来可视化测试用例结构，或查看下方的测试点预览
            </Typography>
          </Box>
          {renderSimpleTestPoints()}
        </Box>
      )}

      {mindMapData && (
        <Box sx={{ 
          border: '2px solid #e3f2fd', 
          borderRadius: '12px', 
          p: 3, 
          backgroundColor: '#fafafa',
          maxHeight: '700px',
          overflowY: 'auto',
          overflowX: 'auto'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#1976d2', mr: 2 }}>
              🌳 思维导图结构
            </Typography>
            <Chip 
              label="可交互" 
              size="small" 
              sx={{ 
                backgroundColor: '#e3f2fd', 
                color: '#1976d2',
                fontSize: '10px'
              }} 
            />
          </Box>
          
          <Box sx={{ 
            minWidth: '100%',
            pb: 2
          }}>
            {renderMindMapNode(mindMapData)}
          </Box>
          

        </Box>
      )}
      
      {/* 测试用例详情对话框 */}
      {renderTestCaseDetailDialog()}
    </Paper>
  );
};

export default MindMapDisplay;