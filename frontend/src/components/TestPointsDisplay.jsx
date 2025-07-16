import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Chip,
  Card,
  CardContent,
  Button,
  ButtonGroup,
  TextField,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  List as ListIcon,
  AccountTree as MindMapIcon,
  TableChart as TableIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import MindMapDisplay from './MindMapDisplay';

const TestPointsDisplay = ({ testPoints = {} }) => {
  // 状态管理
  const [pointStates, setPointStates] = useState({}); // 存储每个测试点的状态（通过/不通过）
  const [editingPoint, setEditingPoint] = useState(null); // 当前编辑的测试点
  const [editText, setEditText] = useState(''); // 编辑文本
  const [feedbacks, setFeedbacks] = useState({}); // 存储反馈意见
  const [selectedModule, setSelectedModule] = useState(''); // 当前选中的模块
  const [viewMode, setViewMode] = useState('table'); // 视图模式：'table' 或 'mindmap'
  const [overallFeedback, setOverallFeedback] = useState(''); // 存储对所有模块的整体评价
  
  // 表格视图相关状态
  const [tableOrderBy, setTableOrderBy] = useState('module'); // 排序字段
  const [tableOrder, setTableOrder] = useState('asc'); // 排序方向
  const [tableFilterStatus, setTableFilterStatus] = useState('all'); // 状态筛选
  const [tableFilterPriority, setTableFilterPriority] = useState('all'); // 优先级筛选
  const [tableFilterModule, setTableFilterModule] = useState('all'); // 模块筛选
  const [tableFilterTestType, setTableFilterTestType] = useState('all'); // 测试类型筛选
  const [selectedTablePoint, setSelectedTablePoint] = useState(null); // 选中的表格行
  const [tableDetailDialog, setTableDetailDialog] = useState(false); // 详情对话框

  const [searchKeyword, setSearchKeyword] = useState(''); // 搜索关键词
  const [batchSelection, setBatchSelection] = useState([]); // 批量选择
  const [showBatchActions, setShowBatchActions] = useState(false); // 显示批量操作
  const [showCoverageAnalysis, setShowCoverageAnalysis] = useState(false); // 显示覆盖率分析
  const [showQualityMetrics, setShowQualityMetrics] = useState(false); // 显示质量指标
  const [exportFormat, setExportFormat] = useState('excel'); // 导出格式
  const [optimizationRounds, setOptimizationRounds] = useState(3); // 多轮优化轮数
const [roundsProgress, setRoundsProgress] = useState([]); // 多轮动画进度

  // 计算总的测试点数量和统计信息
  const getTotalTestPoints = () => {
    return Object.values(testPoints).reduce((total, points) => {
      return total + (Array.isArray(points) ? points.length : 0);
    }, 0);
  };

  const getPointStats = () => {
    const total = getTotalTestPoints();
    const approved = Object.values(pointStates).filter(state => state === 'approved').length;
    const rejected = Object.values(pointStates).filter(state => state === 'rejected').length;
    const pending = total - approved - rejected;
    return { total, approved, rejected, pending };
  };

  const stats = getPointStats();

  // 处理测试点状态变更
  const handlePointState = (moduleIndex, pointIndex, state) => {
    const key = `${moduleIndex}-${pointIndex}`;
    setPointStates(prev => ({
      ...prev,
      [key]: state
    }));
  };

  // 处理编辑功能
  const handleEditStart = (moduleIndex, pointIndex, currentText) => {
    const key = `${moduleIndex}-${pointIndex}`;
    setEditingPoint(key);
    setEditText(currentText);
  };

  const handleEditSave = (moduleIndex, pointIndex) => {
    const key = `${moduleIndex}-${pointIndex}`;
    // 这里可以添加保存逻辑，比如更新testPoints
    setEditingPoint(null);
    setEditText('');
  };

  const handleEditCancel = () => {
    setEditingPoint(null);
    setEditText('');
  };

  // 处理反馈意见
  const handleFeedbackChange = (moduleIndex, pointIndex, feedback) => {
    const key = `${moduleIndex}-${pointIndex}`;
    setFeedbacks(prev => ({
      ...prev,
      [key]: feedback
    }));
  };

  // 处理整体评价
  const handleOverallFeedbackChange = (feedback) => {
    setOverallFeedback(feedback);
  };

  // 保存整体评价
  const handleSaveOverallFeedback = () => {
    if (overallFeedback.trim()) {
      console.log('保存整体评价:', overallFeedback);
      // TODO: 这里可以调用API保存到后端
    } else {
      console.log('整体评价为空，无需保存');
    }
  };

  // 获取所有模块的失败测试点
  const getAllFailedPoints = () => {
    const allFailedPoints = {};
    Object.keys(testPoints).forEach(moduleName => {
      const modulePoints = testPoints[moduleName] || [];
      const failedPoints = modulePoints.filter((_, index) => {
        const pointKey = `${moduleName}-${index}`;
        return pointStates[pointKey] === 'failed';
      });
      if (failedPoints.length > 0) {
        allFailedPoints[moduleName] = failedPoints;
      }
    });
    return allFailedPoints;
  };

  // 获取所有模块的反馈
  const getAllModuleFeedbacks = () => {
    const allFeedbacks = {};
    Object.keys(testPoints).forEach(moduleName => {
      const moduleFeedbacks = Object.keys(feedbacks)
        .filter(key => key.startsWith(moduleName))
        .reduce((acc, key) => {
          acc[key] = feedbacks[key];
          return acc;
        }, {});
      if (Object.keys(moduleFeedbacks).length > 0) {
        allFeedbacks[moduleName] = moduleFeedbacks;
      }
    });
    return allFeedbacks;
  };

  // 生成测试用例
  const handleGenerateTestCases = (moduleName) => {
    const modulePoints = testPoints[moduleName] || [];
    const passedPoints = modulePoints.filter((_, index) => {
      const pointKey = `${moduleName}-${index}`;
      return pointStates[pointKey] === 'passed';
    });
    
    const rejectedCount = modulePoints.filter((_, index) => {
      const pointKey = `${moduleName}-${index}`;
      return pointStates[pointKey] === 'failed';
    }).length;
    
    if (rejectedCount > 0) {
      alert(`模块 "${moduleName}" 还有 ${rejectedCount} 个测试点未通过审核，请先完成审核或选择回环优化。`);
      return;
    }
    
    if (passedPoints.length === 0) {
      alert(`模块 "${moduleName}" 没有通过审核的测试点，无法生成测试用例。`);
      return;
    }
    
    const testCaseData = {
      moduleName,
      passedPoints,
      pointFeedbacks: Object.keys(feedbacks)
        .filter(key => key.startsWith(moduleName))
        .reduce((acc, key) => {
          acc[key] = feedbacks[key];
          return acc;
        }, {})
    };
    
    console.log('生成测试用例 - 数据:', testCaseData);
    // TODO: 这里可以调用API生成测试用例
  };

  // 回环优化 - 多轮动画进度
  const handleLoopOptimization = async () => {
    const allFailedPoints = getAllFailedPoints();
    if (Object.keys(allFailedPoints).length === 0) {
      alert('所有模块都没有未通过的测试点，无需回环优化。');
      return;
    }
    setRoundsProgress([]);
    for (let i = 1; i <= optimizationRounds; i++) {
      setRoundsProgress(prev => ([...prev, { round: i, status: '生成中', text: `第${i}轮：正在调用功能点生成agent进行用例生成...` }]));
      await new Promise(res => setTimeout(res, 2700));
      setRoundsProgress(prev => ([...prev.slice(0, i-1), { round: i, status: '已完成', text: `第${i}轮：用例已生成，正在调用功能点评估agent进行用例评估...` }]));
      await new Promise(res => setTimeout(res, 2700));
      setRoundsProgress(prev => ([...prev.slice(0, i-1), { round: i, status: '已完成', text: `第${i}轮：正在进行第${i}轮的回环优化...` }]));
      await new Promise(res => setTimeout(res, 2600));
      setRoundsProgress(prev => ([...prev.slice(0, i-1), { round: i, status: '已完成', text: `第${i}轮：回环优化已完成` }, ...prev.slice(i)]));
    }
    setRoundsProgress(prev => ([...prev, { round: '全部', status: '已完成', text: `全部${optimizationRounds}轮回环优化已完成！` }]));
  };

  // 处理模块切换
  const handleModuleChange = (event, newValue) => {
    setSelectedModule(newValue);
  };

  // 处理视图模式切换
  const handleViewModeChange = (event, newViewMode) => {
    if (newViewMode !== null) {
      setViewMode(newViewMode);
    }
  };

  // 将testPoints转换为适合思维导图的格式 - 以功能为主干，按场景分支展开
  const convertToMindMapFormat = () => {
    // 创建根节点
    const rootNode = {
      name: '功能测试用例',
      description: '系统功能测试用例总览',
      children: []
    };
    
    // 为每个模块创建功能节点
    Object.keys(testPoints).forEach(moduleName => {
      const points = testPoints[moduleName] || [];
      if (Array.isArray(points) && points.length > 0) {
        // 按场景类型对测试点进行分类
        const scenarioGroups = {};
        
        points.forEach((point, index) => {
          const pointKey = `${moduleName}-${index}`;
          const status = pointStates[pointKey] || 'pending';
          const feedback = feedbacks[pointKey] || '';
          
          // 判断场景类型
          let scenarioType = '功能测试';
          if (point.includes('异常') || point.includes('错误') || point.includes('失败')) {
            scenarioType = '异常测试';
          } else if (point.includes('边界') || point.includes('极限') || point.includes('最大') || point.includes('最小')) {
            scenarioType = '边界测试';
          } else if (point.includes('性能') || point.includes('响应时间') || point.includes('并发')) {
            scenarioType = '性能测试';
          } else if (point.includes('安全') || point.includes('权限') || point.includes('认证')) {
            scenarioType = '安全测试';
          } else if (point.includes('界面') || point.includes('UI') || point.includes('交互')) {
            scenarioType = 'UI测试';
          }
          
          // 判断优先级
          let priority = 'Medium';
          if (point.includes('核心') || point.includes('关键') || point.includes('重要')) {
            priority = 'High';
          } else if (point.includes('可选') || point.includes('辅助') || point.includes('次要')) {
            priority = 'Low';
          }
          
          if (!scenarioGroups[scenarioType]) {
            scenarioGroups[scenarioType] = [];
          }
          
          scenarioGroups[scenarioType].push({
            name: point.length > 50 ? point.substring(0, 50) + '...' : point,
            description: point,
            priority,
            status,
            feedback,
            moduleIndex: moduleName,
            pointIndex: index,
            fullContent: point,
            steps: [
              {
                step_number: 1,
                description: '准备测试环境和数据',
                expected_result: '测试环境就绪'
              },
              {
                step_number: 2,
                description: point,
                expected_result: '功能正常运行，符合预期结果'
              },
              {
                step_number: 3,
                description: '验证结果并清理测试数据',
                expected_result: '测试结果正确，环境清理完成'
              }
            ]
          });
        });
        
        // 创建模块节点
        const moduleNode = {
          name: moduleName,
          description: `${moduleName}功能模块，包含${points.length}个测试点`,
          children: []
        };
        
        // 为每个场景类型创建分支节点
        Object.keys(scenarioGroups).forEach(scenarioType => {
          const scenarioNode = {
            name: scenarioType,
            description: `${scenarioType}场景，包含${scenarioGroups[scenarioType].length}个测试用例`,
            children: scenarioGroups[scenarioType]
          };
          moduleNode.children.push(scenarioNode);
        });
        
        rootNode.children.push(moduleNode);
      }
    });
    
    return rootNode;
  };

  // 将testPoints转换为适合表格的格式
  const convertToTableFormat = () => {
    const tableData = [];
    Object.keys(testPoints).forEach(moduleName => {
      const points = testPoints[moduleName] || [];
      if (Array.isArray(points)) {
        points.forEach((point, index) => {
          const pointKey = `${moduleName}-${index}`;
          const status = pointStates[pointKey] || 'pending';
          const feedback = feedbacks[pointKey] || '';
          
          // 详细的测试类型分类
          let testType = '正向测试';
          let scenarioType = '功能测试';
          
          // 测试类型判断（正向/逆向/边界）
          if (point.includes('异常') || point.includes('错误') || point.includes('失败') || 
              point.includes('无效') || point.includes('非法') || point.includes('不存在') ||
              point.includes('空值') || point.includes('null') || point.includes('负数')) {
            testType = '逆向测试';
          } else if (point.includes('边界') || point.includes('极限') || point.includes('最大') || 
                     point.includes('最小') || point.includes('临界') || point.includes('上限') ||
                     point.includes('下限') || point.includes('0') || point.includes('999')) {
            testType = '边界测试';
          }
          
          // 场景类型判断
          if (point.includes('性能') || point.includes('响应时间') || point.includes('并发') ||
              point.includes('负载') || point.includes('压力') || point.includes('吞吐量')) {
            scenarioType = '性能测试';
          } else if (point.includes('安全') || point.includes('权限') || point.includes('认证') ||
                     point.includes('授权') || point.includes('加密') || point.includes('防护')) {
            scenarioType = '安全测试';
          } else if (point.includes('界面') || point.includes('UI') || point.includes('交互') ||
                     point.includes('显示') || point.includes('布局') || point.includes('样式')) {
            scenarioType = 'UI测试';
          } else if (point.includes('兼容') || point.includes('浏览器') || point.includes('设备') ||
                     point.includes('系统') || point.includes('版本')) {
            scenarioType = '兼容性测试';
          } else if (point.includes('接口') || point.includes('API') || point.includes('数据') ||
                     point.includes('传输') || point.includes('协议')) {
            scenarioType = '接口测试';
          } else if (testType === '逆向测试') {
            scenarioType = '异常测试';
          } else if (testType === '边界测试') {
            scenarioType = '边界测试';
          }
          
          // 优先级判断
          let priority = 'Medium';
          if (point.includes('核心') || point.includes('关键') || point.includes('重要') ||
              point.includes('主要') || point.includes('必须') || point.includes('基础')) {
            priority = 'High';
          } else if (point.includes('可选') || point.includes('辅助') || point.includes('次要') ||
                     point.includes('补充') || point.includes('扩展')) {
            priority = 'Low';
          }
          
          // 复杂度评估
          let complexity = 'Simple';
          if (point.length > 100 || point.includes('复杂') || point.includes('多步骤') ||
              point.includes('集成') || point.includes('流程') || point.includes('组合')) {
            complexity = 'Complex';
          } else if (point.length > 50 || point.includes('中等') || point.includes('配置') ||
                     point.includes('验证') || point.includes('检查')) {
            complexity = 'Medium';
          }
          
          tableData.push({
            id: pointKey,
            module: moduleName,
            content: point,
            testType,
            scenarioType,
            priority,
            complexity,
            status,
            feedback,
            index,
            createdTime: new Date().toISOString().split('T')[0] // 模拟创建时间
          });
        });
      }
    });
    return tableData;
  };

  // 表格排序处理
  const handleTableSort = (property) => {
    const isAsc = tableOrderBy === property && tableOrder === 'asc';
    setTableOrder(isAsc ? 'desc' : 'asc');
    setTableOrderBy(property);
  };

  // 表格数据筛选和排序
  const getFilteredAndSortedTableData = () => {
    let data = convertToTableFormat();
    
    // 搜索关键词筛选
    if (searchKeyword.trim()) {
      const keyword = searchKeyword.toLowerCase();
      data = data.filter(item => 
        item.content.toLowerCase().includes(keyword) ||
        item.module.toLowerCase().includes(keyword) ||
        item.scenarioType.toLowerCase().includes(keyword)
      );
    }
    
    // 模块筛选
    if (tableFilterModule !== 'all') {
      data = data.filter(item => item.module === tableFilterModule);
    }
    
    // 测试类型筛选
    if (tableFilterTestType !== 'all') {
      data = data.filter(item => item.testType === tableFilterTestType);
    }
    
    // 状态筛选
    if (tableFilterStatus !== 'all') {
      data = data.filter(item => item.status === tableFilterStatus);
    }
    
    // 优先级筛选
    if (tableFilterPriority !== 'all') {
      data = data.filter(item => item.priority === tableFilterPriority);
    }
    
    // 排序
    data.sort((a, b) => {
      let aValue = a[tableOrderBy];
      let bValue = b[tableOrderBy];
      
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (tableOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });
    
    return data;
  };

  // 处理表格行点击
  const handleTableRowClick = (point) => {
    setSelectedTablePoint(point);
    setTableDetailDialog(true);
  };

  // 关闭详情对话框
  const handleCloseDetailDialog = () => {
    setTableDetailDialog(false);
    setSelectedTablePoint(null);
  };

  // 批量操作函数
  const handleBatchSelect = (pointId, checked) => {
    if (checked) {
      setBatchSelection(prev => [...prev, pointId]);
    } else {
      setBatchSelection(prev => prev.filter(id => id !== pointId));
    }
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = getFilteredAndSortedTableData().map(item => item.id);
      setBatchSelection(allIds);
    } else {
      setBatchSelection([]);
    }
  };

  const handleBatchApprove = () => {
    batchSelection.forEach(pointId => {
      const [moduleName, pointIndex] = pointId.split('-');
      const key = `${moduleName}-${pointIndex}`;
      setPointStates(prev => ({ ...prev, [key]: 'passed' }));
    });
    setBatchSelection([]);
    setShowBatchActions(false);
  };

  const handleBatchReject = () => {
    batchSelection.forEach(pointId => {
      const [moduleName, pointIndex] = pointId.split('-');
      const key = `${moduleName}-${pointIndex}`;
      setPointStates(prev => ({ ...prev, [key]: 'failed' }));
    });
    setBatchSelection([]);
    setShowBatchActions(false);
  };

  // 覆盖率分析
  const getCoverageAnalysis = () => {
    const data = getFilteredAndSortedTableData();
    const modules = [...new Set(data.map(item => item.module))];
    const testTypes = ['正向测试', '逆向测试', '边界测试'];
    const scenarioTypes = ['功能测试', '性能测试', '安全测试', 'UI测试', '兼容性测试', '接口测试', '异常测试', '边界测试'];
    
    const moduleCoverage = modules.map(module => {
      const moduleData = data.filter(item => item.module === module);
      const typesCovered = testTypes.filter(type => 
        moduleData.some(item => item.testType === type)
      ).length;
      const scenariosCovered = scenarioTypes.filter(scenario => 
        moduleData.some(item => item.scenarioType === scenario)
      ).length;
      
      return {
        module,
        testCount: moduleData.length,
        typeCoverage: (typesCovered / testTypes.length * 100).toFixed(1),
        scenarioCoverage: (scenariosCovered / scenarioTypes.length * 100).toFixed(1),
        passRate: (moduleData.filter(item => item.status === 'passed').length / moduleData.length * 100).toFixed(1)
      };
    });
    
    return { moduleCoverage, totalModules: modules.length, totalTests: data.length };
  };

  // 质量指标分析
  const getQualityMetrics = () => {
    const data = getFilteredAndSortedTableData();
    const highPriorityTests = data.filter(item => item.priority === 'High').length;
    const complexTests = data.filter(item => item.complexity === 'High').length;
    const automationCandidates = data.filter(item => 
      item.testType === '正向测试' && item.complexity !== 'High'
    ).length;
    
    return {
      totalTests: data.length,
      highPriorityRatio: (highPriorityTests / data.length * 100).toFixed(1),
      complexityRatio: (complexTests / data.length * 100).toFixed(1),
      automationPotential: (automationCandidates / data.length * 100).toFixed(1),
      avgTestsPerModule: (data.length / [...new Set(data.map(item => item.module))].length).toFixed(1)
    };
  };

  // 导出功能
  const handleExport = (format) => {
    const data = getFilteredAndSortedTableData();
    const exportData = data.map(item => ({
      '模块': item.module,
      '测试点内容': item.content,
      '测试类型': item.testType,
      '场景类型': item.scenarioType,
      '优先级': item.priority,
      '复杂度': item.complexity,
      '状态': item.status === 'passed' ? '通过' : item.status === 'failed' ? '不通过' : '待审核',
      '创建时间': item.createdTime,
      '反馈': item.feedback
    }));
    
    if (format === 'excel') {
      // 这里可以集成导出到Excel的功能
      console.log('导出到Excel:', exportData);
      alert('Excel导出功能开发中...');
    } else if (format === 'csv') {
      const csv = [Object.keys(exportData[0]).join(',')]
        .concat(exportData.map(row => Object.values(row).join(',')))
        .join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `测试点数据_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
    }
  };

  // 获取状态显示文本和颜色
  const getStatusDisplay = (status) => {
    switch (status) {
      case 'passed':
        return { text: '通过', color: '#4caf50', bgColor: '#e8f5e8' };
      case 'failed':
        return { text: '不通过', color: '#f44336', bgColor: '#ffebee' };
      default:
        return { text: '待审核', color: '#ff9800', bgColor: '#fff3e0' };
    }
  };

  // 获取优先级显示文本和颜色
  const getPriorityDisplay = (priority) => {
    switch (priority) {
      case 'High':
        return { text: '高', color: '#f44336', bgColor: '#ffebee' };
      case 'Low':
        return { text: '低', color: '#4caf50', bgColor: '#e8f5e8' };
      default:
        return { text: '中', color: '#ff9800', bgColor: '#fff3e0' };
    }
  };

  // 初始化选中第一个模块
  useEffect(() => {
    const modules = Object.keys(testPoints);
    if (modules.length > 0 && !selectedModule) {
      setSelectedModule(modules[0]);
    }
  }, [testPoints, selectedModule]);

  if (!testPoints || Object.keys(testPoints).length === 0) {
    return (
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mt: 3, 
          borderRadius: 2,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
        }}
      >
        <Typography variant="h6" color="text.secondary" align="center">
          暂无功能测试点
        </Typography>
      </Paper>
    );
  }

  const modules = Object.keys(testPoints);
  const currentModulePoints = selectedModule ? testPoints[selectedModule] || [] : [];

  return (
    <Paper 
      elevation={1} 
      sx={{ 
        p: 2.5, 
        mt: 2,
        borderRadius: 3,
        backgroundColor: '#ffffff',
        border: '1px solid #e0e0e0'
      }}
    >
      {/* 头部控制区域 */}
       <Box sx={{ mb: 3 }}>
         {/* 视图切换和统计信息在同一行 */}
         <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 2 }}>
           {/* 视图切换按钮 */}
           <ToggleButtonGroup
             value={viewMode}
             exclusive
             onChange={handleViewModeChange}
             size="small"
             sx={{
               '& .MuiToggleButton-root': {
                 textTransform: 'none',
                 borderColor: '#1976d2',
                 color: '#1976d2',
                 '&.Mui-selected': {
                   backgroundColor: '#1976d2',
                   color: 'white',
                   '&:hover': {
                     backgroundColor: '#1565c0'
                   }
                 }
               }
             }}
           >
             <ToggleButton value="table">
               <TableIcon sx={{ mr: 1 }} />
               表格视图
             </ToggleButton>
             <ToggleButton value="mindmap">
               <MindMapIcon sx={{ mr: 1 }} />
               思维导图
             </ToggleButton>
           </ToggleButtonGroup>
           
           {/* 统计信息 */}
           <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
             <Chip 
               label={`总计 ${stats.total}`}
               variant="outlined"
               size="small"
               sx={{ borderColor: '#1976d2', color: '#1976d2', fontWeight: 500 }}
             />
             <Chip 
               label={`通过 ${stats.approved}`}
               size="small"
               sx={{ backgroundColor: '#e8f5e8', color: '#2e7d32', fontWeight: 500 }}
             />
             <Chip 
               label={`不通过 ${stats.rejected}`}
               size="small"
               sx={{ backgroundColor: '#ffebee', color: '#d32f2f', fontWeight: 500 }}
             />
             <Chip 
               label={`待审核 ${stats.pending}`}
               size="small"
               sx={{ backgroundColor: '#fff3e0', color: '#f57c00', fontWeight: 500 }}
             />
           </Box>
         </Box>
       </Box>

      {/* 模块标签页 */}
      {viewMode !== 'table' && (
        <Box sx={{ mb: 2 }}>
          <Tabs 
            value={selectedModule} 
            onChange={handleModuleChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              '& .MuiTabs-indicator': {
                backgroundColor: '#1976d2'
              },
              '& .MuiTabs-root': {
                minHeight: 40
              }
            }}
          >
            {modules.map((moduleName) => {
                const modulePoints = testPoints[moduleName] || [];
                const modulePointCount = Array.isArray(modulePoints) ? modulePoints.length : 0;
                return (
                  <Tab 
                    key={moduleName}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {moduleName}
                        </Typography>
                        <Chip 
                          size="small"
                          label={modulePointCount}
                          sx={{ 
                            height: 20,
                            fontSize: '0.75rem',
                            backgroundColor: '#e3f2fd',
                            color: '#1976d2'
                          }}
                        />
                      </Box>
                    }
                    value={moduleName}
                    sx={{
                      textTransform: 'none',
                      minHeight: 48,
                      '&.Mui-selected': {
                        color: '#1976d2'
                      }
                    }}
                  />
                );
              })}
          </Tabs>
        </Box>
      )}

      <Divider sx={{ backgroundColor: '#e0e0e0', mb: 2 }} />

      {/* 根据视图模式显示不同内容 */}
      {viewMode === 'mindmap' ? (
          <MindMapDisplay testPoints={convertToMindMapFormat()} />
        ) : viewMode === 'table' ? (
        <Box>
          {/* 搜索和筛选器 */}
          <Box sx={{ mb: 1.5, p: 1.5, bgcolor: '#f8f9fa', borderRadius: 1 }}>
            {/* 搜索框和功能按钮在同一行 */}
            <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mb: 1.5 }}>
              <TextField
                size="small"
                placeholder="搜索测试点内容、模块名称或场景类型..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <Box sx={{ mr: 1, color: '#666' }}>🔍</Box>
                  ),
                  endAdornment: searchKeyword && (
                    <IconButton
                      size="small"
                      onClick={() => setSearchKeyword('')}
                      sx={{ p: 0.5 }}
                    >
                      ❌
                    </IconButton>
                  )
                }}
                sx={{
                  flex: 1,
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'white',
                    '&:hover': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#1976d2'
                      }
                    }
                  }
                }}
              />
              
              {/* 功能按钮 */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setShowCoverageAnalysis(!showCoverageAnalysis)}
                  startIcon={showCoverageAnalysis ? '📊' : '📈'}
                >
                  覆盖率指标
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setShowQualityMetrics(!showQualityMetrics)}
                  startIcon={showQualityMetrics ? '🎯' : '📋'}
                >
                  质量指标
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setShowBatchActions(!showBatchActions)}
                  startIcon={showBatchActions ? '✅' : '☑️'}
                >
                  批量操作
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleExport('csv')}
                  startIcon={'📤'}
                >
                  导出CSV
                </Button>
              </Box>
            </Box>

            {/* 筛选器 - 四个筛选项在一排 */}
            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
              <FormControl size="small" sx={{ minWidth: 110 }}>
                <InputLabel>状态</InputLabel>
                <Select
                  value={tableFilterStatus}
                  label="状态"
                  onChange={(e) => setTableFilterStatus(e.target.value)}
                >
                  <MenuItem value="all">全部状态</MenuItem>
                  <MenuItem value="pending">待审核</MenuItem>
                  <MenuItem value="passed">通过</MenuItem>
                  <MenuItem value="failed">不通过</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 110 }}>
                <InputLabel>优先级</InputLabel>
                <Select
                  value={tableFilterPriority}
                  label="优先级"
                  onChange={(e) => setTableFilterPriority(e.target.value)}
                >
                  <MenuItem value="all">全部优先级</MenuItem>
                  <MenuItem value="High">高</MenuItem>
                  <MenuItem value="Medium">中</MenuItem>
                  <MenuItem value="Low">低</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 130 }}>
                <InputLabel>功能模块</InputLabel>
                <Select
                  value={tableFilterModule}
                  label="功能模块"
                  onChange={(e) => setTableFilterModule(e.target.value)}
                >
                  <MenuItem value="all">全部模块</MenuItem>
                  {Object.keys(testPoints).map(moduleName => (
                    <MenuItem key={moduleName} value={moduleName}>{moduleName}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 130 }}>
                <InputLabel>测试类型</InputLabel>
                <Select
                  value={tableFilterTestType}
                  label="测试类型"
                  onChange={(e) => setTableFilterTestType(e.target.value)}
                >
                  <MenuItem value="all">全部类型</MenuItem>
                  <MenuItem value="正向测试">正向测试</MenuItem>
                  <MenuItem value="逆向测试">逆向测试</MenuItem>
                  <MenuItem value="边界测试">边界测试</MenuItem>
                </Select>
              </FormControl>

              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setSearchKeyword('');
                  setTableFilterModule('all');
                  setTableFilterTestType('all');
                  setTableFilterStatus('all');
                  setTableFilterPriority('all');
                }}
                sx={{ ml: 'auto' }}
              >
                重置筛选
              </Button>
            </Box>
          </Box>

           {/* 覆盖率分析面板 */}
           {showCoverageAnalysis && (
             <Card sx={{ mb: 1.5, border: '1px solid #e3f2fd' }}>
               <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                 <Typography variant="h6" sx={{ mb: 1.5, color: '#1976d2', display: 'flex', alignItems: 'center', gap: 1 }}>
                   📊 测试覆盖率分析
                 </Typography>
                 <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 1.5 }}>
                   {getCoverageAnalysis().moduleCoverage.map((module, index) => (
                     <Card key={index} variant="outlined" sx={{ p: 1.5 }}>
                       <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>{module.module}</Typography>
                       <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.8 }}>
                         <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                           <Typography variant="body2">测试用例数:</Typography>
                           <Chip label={module.testCount} size="small" color="primary" />
                         </Box>
                         <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                           <Typography variant="body2">类型覆盖率:</Typography>
                           <Chip label={`${module.typeCoverage}%`} size="small" color={module.typeCoverage >= 80 ? 'success' : module.typeCoverage >= 60 ? 'warning' : 'error'} />
                         </Box>
                         <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                           <Typography variant="body2">场景覆盖率:</Typography>
                           <Chip label={`${module.scenarioCoverage}%`} size="small" color={module.scenarioCoverage >= 80 ? 'success' : module.scenarioCoverage >= 60 ? 'warning' : 'error'} />
                         </Box>
                         <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                           <Typography variant="body2">通过率:</Typography>
                           <Chip label={`${module.passRate}%`} size="small" color={module.passRate >= 80 ? 'success' : module.passRate >= 60 ? 'warning' : 'error'} />
                         </Box>
                       </Box>
                     </Card>
                   ))}
                 </Box>
               </CardContent>
             </Card>
           )}

           {/* 质量指标面板 */}
           {showQualityMetrics && (
             <Card sx={{ mb: 1.5, border: '1px solid #e8f5e9' }}>
               <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                 <Typography variant="h6" sx={{ mb: 1.5, color: '#388e3c', display: 'flex', alignItems: 'center', gap: 1 }}>
                   🎯 测试质量指标
                 </Typography>
                 <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 1.5 }}>
                   {(() => {
                     const metrics = getQualityMetrics();
                     return [
                       { label: '总测试用例', value: metrics.totalTests, unit: '个', color: 'primary' },
                       { label: '高优先级占比', value: metrics.highPriorityRatio, unit: '%', color: 'error' },
                       { label: '高复杂度占比', value: metrics.complexityRatio, unit: '%', color: 'warning' },
                       { label: '自动化潜力', value: metrics.automationPotential, unit: '%', color: 'success' },
                       { label: '平均用例/模块', value: metrics.avgTestsPerModule, unit: '个', color: 'info' }
                     ].map((metric, index) => (
                       <Card key={index} variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                         <Typography variant="h4" sx={{ color: `${metric.color}.main`, fontWeight: 'bold' }}>
                           {metric.value}{metric.unit}
                         </Typography>
                         <Typography variant="body2" color="text.secondary">
                           {metric.label}
                         </Typography>
                       </Card>
                     ));
                   })()}
                 </Box>
               </CardContent>
             </Card>
           )}

           {/* 批量操作面板 */}
           {showBatchActions && (
             <Card sx={{ mb: 1.5, border: '1px solid #fff3e0' }}>
               <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                 <Typography variant="h6" sx={{ mb: 1.5, color: '#f57c00', display: 'flex', alignItems: 'center', gap: 1 }}>
                   ✅ 批量操作
                 </Typography>
                 <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
                   <Typography variant="body2">
                     已选择 {batchSelection.length} 项
                   </Typography>
                   <Button
                     variant="contained"
                     size="small"
                     color="success"
                     onClick={handleBatchApprove}
                     disabled={batchSelection.length === 0}
                   >
                     批量通过
                   </Button>
                   <Button
                     variant="contained"
                     size="small"
                     color="error"
                     onClick={handleBatchReject}
                     disabled={batchSelection.length === 0}
                   >
                     批量拒绝
                   </Button>
                   <Button
                     variant="outlined"
                     size="small"
                     onClick={() => setBatchSelection([])}
                     disabled={batchSelection.length === 0}
                   >
                     清空选择
                   </Button>
                 </Box>
               </CardContent>
             </Card>
           )}
 
           {/* 表格 */}
           <TableContainer component={Paper} sx={{ maxHeight: 'calc(100vh - 280px)', border: '1px solid #e0e0e0' }}>
            <Table stickyHeader size="small">
              <TableHead>
                  <TableRow sx={{ '& .MuiTableCell-root': { py: 0.5, fontSize: '0.875rem' } }}>
                  {showBatchActions && (
                    <TableCell sx={{ fontWeight: 600, width: 50 }}>
                      <Checkbox
                        checked={batchSelection.length === getFilteredAndSortedTableData().length && getFilteredAndSortedTableData().length > 0}
                        indeterminate={batchSelection.length > 0 && batchSelection.length < getFilteredAndSortedTableData().length}
                        onChange={handleSelectAll}
                        size="small"
                      />
                    </TableCell>
                  )}
                  <TableCell>
                    <TableSortLabel
                      active={tableOrderBy === 'module'}
                      direction={tableOrderBy === 'module' ? tableOrder : 'asc'}
                      onClick={() => handleTableSort('module')}
                      sx={{ fontWeight: 600 }}
                    >
                      功能点
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={tableOrderBy === 'scenarioType'}
                      direction={tableOrderBy === 'scenarioType' ? tableOrder : 'asc'}
                      onClick={() => handleTableSort('scenarioType')}
                      sx={{ fontWeight: 600 }}
                    >
                      场景类型
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={tableOrderBy === 'priority'}
                      direction={tableOrderBy === 'priority' ? tableOrder : 'asc'}
                      onClick={() => handleTableSort('priority')}
                      sx={{ fontWeight: 600 }}
                    >
                      优先级
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={tableOrderBy === 'status'}
                      direction={tableOrderBy === 'status' ? tableOrder : 'asc'}
                      onClick={() => handleTableSort('status')}
                      sx={{ fontWeight: 600 }}
                    >
                      确认状态
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>测试点内容</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {getFilteredAndSortedTableData().map((row) => {
                  const statusDisplay = getStatusDisplay(row.status);
                  const priorityDisplay = getPriorityDisplay(row.priority);
                  
                  return (
                    <TableRow 
                      key={row.id}
                      hover
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { backgroundColor: '#f5f5f5' },
                        backgroundColor: batchSelection.includes(row.id) ? '#e3f2fd' : 'inherit'
                      }}
                    >
                      {showBatchActions && (
                        <TableCell>
                          <Checkbox
                            checked={batchSelection.includes(row.id)}
                            onChange={() => handleBatchSelect(row.id)}
                            size="small"
                          />
                        </TableCell>
                      )}
                      <TableCell sx={{ fontWeight: 500, color: '#1976d2' }}>
                        {row.module}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={row.scenarioType}
                          size="small"
                          variant="outlined"
                          sx={{ 
                            borderColor: '#2196f3',
                            color: '#2196f3',
                            fontSize: '0.75rem'
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={priorityDisplay.text}
                          size="small"
                          sx={{ 
                            backgroundColor: priorityDisplay.bgColor,
                            color: priorityDisplay.color,
                            fontSize: '0.75rem',
                            fontWeight: 500
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={statusDisplay.text}
                          size="small"
                          sx={{ 
                            backgroundColor: statusDisplay.bgColor,
                            color: statusDisplay.color,
                            fontSize: '0.75rem',
                            fontWeight: 500
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ maxWidth: 300 }}>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {row.content}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleTableRowClick(row)}
                          sx={{ textTransform: 'none' }}
                        >
                          查看详情
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      ) : (
        /* 列表视图 - 当前模块的测试点列表 */
        selectedModule && currentModulePoints.length > 0 && (
        <Box>
          <Typography 
            variant="h6" 
            sx={{ 
              mb: 2, 
              color: '#333',
              fontWeight: 600
            }}
          >
            {selectedModule} - 测试点列表
          </Typography>
          {currentModulePoints.map((point, pointIndex) => {
            const pointKey = `${selectedModule}-${pointIndex}`;
            const pointState = pointStates[pointKey];
            const isEditing = editingPoint === pointKey;
            const feedback = feedbacks[pointKey] || '';
            
            return (
              <Card 
                key={pointIndex}
                sx={{ 
                   mb: 2, 
                   backgroundColor: pointState === 'passed' ? '#f1f8e9' : 
                                   pointState === 'failed' ? '#ffebee' : 
                                   '#ffffff',
                   border: pointState === 'passed' ? '1px solid #4caf50' : 
                          pointState === 'failed' ? '1px solid #f44336' : 
                          '1px solid #e0e0e0',
                   borderRadius: 2,
                   boxShadow: 'none'
                 }}
              >
               <CardContent>
                      {/* 测试点内容 */}
                       <Box sx={{ mb: 2 }}>
                         {isEditing ? (
                           <TextField
                             fullWidth
                             multiline
                             rows={2}
                             value={editText}
                             onChange={(e) => setEditText(e.target.value)}
                             variant="outlined"
                             sx={{ 
                               '& .MuiOutlinedInput-root': {
                                 backgroundColor: '#ffffff',
                                 '& fieldset': { borderColor: '#d0d0d0' },
                                 '&:hover fieldset': { borderColor: '#1976d2' },
                                 '&.Mui-focused fieldset': { borderColor: '#1976d2' }
                               }
                             }}
                           />
                         ) : (
                           <Typography 
                             variant="body1" 
                             sx={{ 
                               color: '#333',
                               fontWeight: 400,
                               lineHeight: 1.6,
                               mb: 1
                             }}
                           >
                             {point}
                           </Typography>
                         )}
                       </Box>
                      
                      {/* 操作按钮 */}
                       <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                         {isEditing ? (
                           <>
                             <Button
                               size="small"
                               variant="contained"
                               color="success"
                               startIcon={<SaveIcon />}
                               onClick={() => handleEditSave(selectedModule, pointIndex)}
                               sx={{ textTransform: 'none' }}
                             >
                               保存
                             </Button>
                             <Button
                               size="small"
                               variant="outlined"
                               startIcon={<CancelIcon />}
                               onClick={handleEditCancel}
                               sx={{ textTransform: 'none', color: '#666', borderColor: '#d0d0d0' }}
                             >
                               取消
                             </Button>
                           </>
                         ) : (
                           <>
                             <ButtonGroup size="small" variant="outlined">
                               <Button
                                 color={pointState === 'passed' ? 'success' : 'inherit'}
                                 onClick={() => handlePointState(selectedModule, pointIndex, 'passed')}
                                 sx={{ 
                                   textTransform: 'none',
                                   backgroundColor: pointState === 'passed' ? '#4caf50' : 'transparent',
                                   color: pointState === 'passed' ? 'white' : '#4caf50',
                                   border: '1px solid #4caf50',
                                   '&:hover': {
                                     backgroundColor: '#4caf50',
                                     color: 'white'
                                   }
                                 }}
                               >
                                 通过
                               </Button>
                               <Button
                                 color={pointState === 'failed' ? 'error' : 'inherit'}
                                 onClick={() => handlePointState(selectedModule, pointIndex, 'failed')}
                                 sx={{ 
                                   textTransform: 'none',
                                   backgroundColor: pointState === 'failed' ? '#f44336' : 'transparent',
                                   color: pointState === 'failed' ? 'white' : '#f44336',
                                   border: '1px solid #f44336',
                                   '&:hover': {
                                     backgroundColor: '#f44336',
                                     color: 'white'
                                   }
                                 }}
                               >
                                 不通过
                               </Button>
                             </ButtonGroup>
                             
                             <Tooltip title="编辑测试点">
                               <IconButton
                                 size="small"
                                 onClick={() => handleEditStart(selectedModule, pointIndex, point)}
                                 sx={{ color: '#666', '&:hover': { color: '#1976d2' } }}
                               >
                                 <EditIcon />
                               </IconButton>
                             </Tooltip>
                           </>
                         )}
                       </Box>
                      
                      {/* 反馈意见输入框 */}
                       <TextField
                         fullWidth
                         size="small"
                         placeholder="输入修改意见或反馈..."
                         value={feedback}
                         onChange={(e) => handleFeedbackChange(selectedModule, pointIndex, e.target.value)}
                         variant="outlined"
                         multiline
                         rows={2}
                         sx={{ 
                           '& .MuiOutlinedInput-root': {
                             backgroundColor: '#f9f9f9',
                             '& fieldset': { borderColor: '#e0e0e0' },
                             '&:hover fieldset': { borderColor: '#bdbdbd' },
                             '&.Mui-focused fieldset': { borderColor: '#1976d2' }
                           },
                           '& .MuiInputBase-input::placeholder': {
                             color: '#999',
                             opacity: 1
                           }
                         }}
                       />
                    </CardContent>
                  </Card>
                );
              })}        </Box>
        )
      )}


      
      {/* 底部全局操作区域 */}
      <Box sx={{ mt: 3 }}>
        {/* 全局操作区域 */}
        <Card sx={{ mb: 2, backgroundColor: '#fff3cd', border: '1px solid #ffeaa7' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1.5, color: '#856404', fontWeight: 600 }}>
              整体优化意见
            </Typography>
            
            <TextField
               fullWidth
               multiline
               rows={2}
               placeholder="请输入对所有功能模块的整体评价和建议..."
               variant="outlined"
               value={overallFeedback}
               onChange={(e) => handleOverallFeedbackChange(e.target.value)}
               sx={{
                 mb: 1.5,
                 '& .MuiOutlinedInput-root': {
                   backgroundColor: '#ffffff',
                   '& fieldset': { borderColor: '#ffeaa7' },
                   '&:hover fieldset': { borderColor: '#f39c12' },
                   '&.Mui-focused fieldset': { borderColor: '#f39c12' }
                 },
                 '& .MuiInputBase-input::placeholder': {
                   color: '#856404',
                   opacity: 0.7
                 }
               }}
             />
            
            <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center', flexWrap: 'wrap', alignItems: 'center' }}>
               <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                 <Button
                   variant="contained"
                   sx={{ 
                     textTransform: 'none',
                     minWidth: 140,
                     backgroundColor: '#f39c12',
                     color: '#ffffff',
                     '&:hover': { backgroundColor: '#e67e22' }
                   }}
                   onClick={handleLoopOptimization}
                 >
                   多轮自动化优化
                 </Button>
                 
                 <TextField
                   type="number"
                   size="small"
                   value={optimizationRounds}
                   onChange={(e) => setOptimizationRounds(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                   inputProps={{ 
                     min: 1, 
                     max: 10,
                     style: { textAlign: 'center', width: '60px' }
                   }}
                   sx={{
                     width: '80px',
                     '& .MuiOutlinedInput-root': {
                       backgroundColor: '#ffffff',
                       '& fieldset': { borderColor: '#f39c12' },
                       '&:hover fieldset': { borderColor: '#e67e22' },
                       '&.Mui-focused fieldset': { borderColor: '#e67e22' }
                     }
                   }}
                 />
                 
                 <Typography variant="body2" sx={{ color: '#856404', fontWeight: 500 }}>
                   轮
                 </Typography>
               </Box>
            </Box>
          </CardContent>
    </Card>

    {/* 多轮自动化优化动画进度展示 */}
    {roundsProgress.length > 0 && (
      <Box sx={{ mt: 2, mb: 2 }}>
        <Typography variant="h6">多轮自动优化进度</Typography>
        {roundsProgress.map((item, idx) => (
          <Box key={idx} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Chip label={`第${item.round}轮`} color={item.status === '已完成' ? 'success' : 'primary'} sx={{ mr: 1 }} />
            <Box sx={{ flex: 1, mx: 2 }}>
              <Box sx={{ width: '100%', background: '#eee', borderRadius: 2, overflow: 'hidden', height: 12 }}>
                <Box sx={{
                  width: item.status === '生成中' ? `${(Math.abs(Math.sin(Date.now() / 300 + idx)) * 60 + 30).toFixed(0)}%` : '100%',
                  background: item.status === '生成中' ? 'linear-gradient(90deg, #42a5f5 40%, #90caf9 100%)' : '#66bb6a',
                  height: '100%',
                  transition: 'width 0.5s',
                  animation: item.status === '生成中' ? 'progressBarAnim 1.2s linear infinite' : 'none'
                }} />
              </Box>
            </Box>
            <Typography variant="body2" color={item.status === '生成中' ? 'primary' : 'success.main'} sx={{ minWidth: 60 }}>
              {item.status}
            </Typography>
            <Typography sx={{ ml: 2 }}>{item.text}</Typography>
          </Box>
        ))}
        <style>{`
          @keyframes progressBarAnim {
            0% { opacity: 0.7; }
            50% { opacity: 1; }
            100% { opacity: 0.7; }
          }
        `}</style>
      </Box>
    )}

    {/* 新增：多轮结果导出为csv按钮 */}
    {roundsProgress.length > 0 && (
      <Box sx={{ mb: 2 }}>
        <Button
          variant="outlined"
          color="primary"
          size="small"
          onClick={() => {
            if (roundsProgress.length === 0) return;
            const exportData = roundsProgress.map(item => ({
              '轮次': item.round,
              '状态': item.status,
              '描述': item.text
            }));
            const csv = [Object.keys(exportData[0]).join(',')]
              .concat(exportData.map(row => Object.values(row).join(',')))
              .join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `多轮优化结果_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
          }}
          sx={{ ml: 1 }}
        >
          将每轮结果导出为csv
        </Button>
      </Box>
    )}

      </Box>
      
      {/* 表格详情对话框 */}
      <Dialog 
        open={tableDetailDialog} 
        onClose={handleCloseDetailDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ borderBottom: '1px solid #e0e0e0' }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            测试点详情
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          {selectedTablePoint && (
            <Box>
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                  功能模块
                </Typography>
                <Chip 
                  label={selectedTablePoint.module}
                  sx={{ 
                    backgroundColor: '#e3f2fd',
                    color: '#1976d2',
                    fontWeight: 500
                  }}
                />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                  测试点内容
                </Typography>
                <Paper sx={{ p: 2, backgroundColor: '#f9f9f9' }}>
                  <Typography variant="body1">
                    {selectedTablePoint.content}
                  </Typography>
                </Paper>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 3, mb: 3 }}>
                <Box>
                  <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                    场景类型
                  </Typography>
                  <Chip 
                    label={selectedTablePoint.scenarioType}
                    variant="outlined"
                    sx={{ 
                      borderColor: '#2196f3',
                      color: '#2196f3'
                    }}
                  />
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                    优先级
                  </Typography>
                  <Chip 
                    label={getPriorityDisplay(selectedTablePoint.priority).text}
                    sx={{ 
                      backgroundColor: getPriorityDisplay(selectedTablePoint.priority).bgColor,
                      color: getPriorityDisplay(selectedTablePoint.priority).color,
                      fontWeight: 500
                    }}
                  />
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                    确认状态
                  </Typography>
                  <Chip 
                    label={getStatusDisplay(selectedTablePoint.status).text}
                    sx={{ 
                      backgroundColor: getStatusDisplay(selectedTablePoint.status).bgColor,
                      color: getStatusDisplay(selectedTablePoint.status).color,
                      fontWeight: 500
                    }}
                  />
                </Box>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                  状态操作
                </Typography>
                <ButtonGroup variant="outlined" size="small">
                  <Button
                    color={selectedTablePoint.status === 'passed' ? 'success' : 'inherit'}
                    onClick={() => {
                      handlePointState(selectedTablePoint.module, selectedTablePoint.index, 'passed');
                      setSelectedTablePoint(prev => ({ ...prev, status: 'passed' }));
                    }}
                    sx={{ 
                      textTransform: 'none',
                      backgroundColor: selectedTablePoint.status === 'passed' ? '#4caf50' : 'transparent',
                      color: selectedTablePoint.status === 'passed' ? 'white' : '#4caf50',
                      border: '1px solid #4caf50',
                      '&:hover': {
                        backgroundColor: '#4caf50',
                        color: 'white'
                      }
                    }}
                  >
                    通过
                  </Button>
                  <Button
                    color={selectedTablePoint.status === 'failed' ? 'error' : 'inherit'}
                    onClick={() => {
                      handlePointState(selectedTablePoint.module, selectedTablePoint.index, 'failed');
                      setSelectedTablePoint(prev => ({ ...prev, status: 'failed' }));
                    }}
                    sx={{ 
                      textTransform: 'none',
                      backgroundColor: selectedTablePoint.status === 'failed' ? '#f44336' : 'transparent',
                      color: selectedTablePoint.status === 'failed' ? 'white' : '#f44336',
                      border: '1px solid #f44336',
                      '&:hover': {
                        backgroundColor: '#f44336',
                        color: 'white'
                      }
                    }}
                  >
                    不通过
                  </Button>
                </ButtonGroup>
              </Box>
              
              {/* 自动化评估建议展示栏 */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                  🤖 自动化评估建议
                </Typography>
                <Paper 
                  sx={{ 
                    p: 2, 
                    backgroundColor: '#f0f8ff',
                    border: '1px solid #e3f2fd',
                    borderRadius: 2
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Chip 
                      label="AI 评估"
                      size="small"
                      sx={{ 
                        backgroundColor: '#2196f3',
                        color: 'white',
                        fontWeight: 500,
                        mr: 1
                      }}
                    />
                    <Typography variant="caption" sx={{ color: '#666' }}>
                      基于AI模型的自动化评估结果
                    </Typography>
                  </Box>
                  
                  {/* 评估结果内容区域 */}
                   <Box sx={{ 
                     p: 1.5,
                     backgroundColor: '#ffffff',
                     borderRadius: 1,
                     border: '1px solid #e8f4fd'
                   }}>
                     <Typography variant="body2" sx={{ 
                       color: '#333',
                       lineHeight: 1.6,
                       fontSize: '0.875rem'
                     }}>
                       该测试点覆盖了核心功能流程，建议优先级设为高。测试步骤清晰，预期结果明确。
                       建议补充异常场景的测试覆盖，如网络异常、数据异常等边界情况。
                     </Typography>
                   </Box>
                </Paper>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" sx={{ color: '#666', mb: 1 }}>
                  反馈意见
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder="输入修改意见或反馈..."
                  value={selectedTablePoint.feedback}
                  onChange={(e) => {
                    const newFeedback = e.target.value;
                    handleFeedbackChange(selectedTablePoint.module, selectedTablePoint.index, newFeedback);
                    setSelectedTablePoint(prev => ({ ...prev, feedback: newFeedback }));
                  }}
                  variant="outlined"
                  sx={{ 
                    '& .MuiOutlinedInput-root': {
                      backgroundColor: '#f9f9f9',
                      '& fieldset': { borderColor: '#e0e0e0' },
                      '&:hover fieldset': { borderColor: '#bdbdbd' },
                      '&.Mui-focused fieldset': { borderColor: '#1976d2' }
                    }
                  }}
                />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid #e0e0e0', p: 2 }}>
          <Button 
            onClick={handleCloseDetailDialog}
            sx={{ textTransform: 'none' }}
          >
            关闭
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 生成最终测试用例按钮 */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          size="large"
          sx={{ 
            textTransform: 'none',
            minWidth: 200,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            backgroundColor: '#28a745',
            '&:hover': { backgroundColor: '#218838' },
            borderRadius: 2,
            boxShadow: '0 4px 12px rgba(40, 167, 69, 0.3)'
          }}
          onClick={handleLoopOptimization}
        >
          生成最终测试用例
        </Button>
      </Box>
    </Paper>
  );
};

export default TestPointsDisplay;