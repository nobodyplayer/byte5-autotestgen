import React from 'react';
import { AppBar, Toolbar, Typography, Chip, Box } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

const Header = ({ serverStatus }) => {
  const getStatusConfig = () => {
    switch (serverStatus) {
      case 'connected':
        return {
          icon: <CheckCircleIcon sx={{ fontSize: 16 }} />,
          label: '服务已连接',
          color: 'success',
          bgcolor: 'success.50',
          borderColor: 'success.200'
        };
      case 'error':
        return {
          icon: <ErrorIcon sx={{ fontSize: 16 }} />,
          label: '连接失败',
          color: 'error',
          bgcolor: 'error.50',
          borderColor: 'error.200'
        };
      default:
        return {
          icon: <HourglassEmptyIcon sx={{ fontSize: 16 }} />,
          label: '连接中',
          color: 'default',
          bgcolor: 'grey.100',
          borderColor: 'grey.300'
        };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <AppBar 
      position="static" 
      elevation={0} 
      sx={{ 
        bgcolor: 'white', 
        borderBottom: '1px solid', 
        borderColor: 'grey.200',
        backdropFilter: 'blur(8px)'
      }}
    >
      <Toolbar sx={{ py: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
          <Box sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            bgcolor: 'primary.main',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <AutoAwesomeIcon sx={{ color: 'white', fontSize: 24 }} />
          </Box>
          <Box>
            <Typography 
              variant="h5" 
              component="div" 
              sx={{ 
                color: 'text.primary', 
                fontWeight: 700,
                lineHeight: 1.2
              }}
            >
              基于多模态模型的测试用例生成器
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: 'text.secondary',
                fontWeight: 500
              }}
            >
              Produce by Byte5
            </Typography>
          </Box>
        </Box>
        <Chip
          icon={statusConfig.icon}
          label={statusConfig.label}
          sx={{
            bgcolor: statusConfig.bgcolor,
            borderColor: statusConfig.borderColor,
            color: `${statusConfig.color}.dark`,
            fontWeight: 500,
            '& .MuiChip-icon': {
              color: `${statusConfig.color}.main`
            }
          }}
          variant="outlined"
          size="small"
        />
      </Toolbar>
    </AppBar>
  );
};

export default Header;
