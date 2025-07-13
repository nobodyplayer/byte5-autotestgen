import React from 'react';
import {
  Paper,
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import FunctionIcon from '@mui/icons-material/Function';

const TestPointsDisplay = ({ testPoints = {} }) => {
  // 计算总的测试点数量
  const getTotalTestPoints = () => {
    return Object.values(testPoints).reduce((total, points) => {
      return total + (Array.isArray(points) ? points.length : 0);
    }, 0);
  };

  const totalPoints = getTotalTestPoints();

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

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 3, 
        mt: 3, 
        borderRadius: 2,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}
    >
      {/* 头部信息 */}
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
          🎯 功能测试点
        </Typography>
        <Chip 
          icon={<FunctionIcon />}
          label={`共生成 ${totalPoints} 个功能测试点`}
          sx={{ 
            backgroundColor: 'rgba(255,255,255,0.2)', 
            color: 'white',
            fontWeight: 'bold'
          }}
        />
      </Box>

      <Divider sx={{ backgroundColor: 'rgba(255,255,255,0.3)', mb: 3 }} />

      {/* 按模块展示测试点 */}
      {Object.entries(testPoints).map(([moduleName, points], moduleIndex) => {
        if (!Array.isArray(points) || points.length === 0) return null;
        
        return (
          <Box key={moduleIndex} sx={{ mb: 4 }}>
            {/* 模块标题 */}
            <Typography 
              variant="h5" 
              sx={{ 
                fontWeight: 'bold', 
                mb: 2,
                color: '#fff',
                borderBottom: '2px solid rgba(255,255,255,0.3)',
                pb: 1
              }}
            >
              📋 {moduleName}
            </Typography>
            
            {/* 测试点列表 */}
            <List sx={{ pl: 2 }}>
              {points.map((point, pointIndex) => (
                <ListItem 
                  key={pointIndex}
                  sx={{ 
                    py: 1,
                    px: 2,
                    mb: 1,
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    borderRadius: 1,
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,0.2)'
                    }
                  }}
                >
                  <ListItemIcon>
                    <CheckCircleIcon sx={{ color: '#4caf50' }} />
                  </ListItemIcon>
                  <ListItemText 
                    primary={
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          color: 'white',
                          fontWeight: 500,
                          lineHeight: 1.6
                        }}
                      >
                        {point}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        );
      })}

      {/* 底部总结 */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>
          ✨ 功能测试点生成完成，可用于后续测试用例设计
        </Typography>
      </Box>
    </Paper>
  );
};

export default TestPointsDisplay;