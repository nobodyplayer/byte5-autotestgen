import React, { useRef, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  LinearProgress,
  Chip,
  Fade
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { styled, keyframes } from '@mui/material/styles';

const StreamingOutput = ({ content }) => {
  const outputRef = useRef(null);

  // 当内容更新时自动滚动到底部
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [content]);

  const pulse = keyframes`
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
    100% {
      opacity: 1;
    }
  `;

  const StyledLinearProgress = styled(LinearProgress)(({ theme }) => ({
    height: 3,
    borderRadius: 2,
    backgroundColor: theme.palette.grey[200],
    '& .MuiLinearProgress-bar': {
      borderRadius: 2,
      background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
    }
  }));

  const StyledMarkdown = styled(Box)(({ theme }) => ({
    '& h1, & h2, & h3': {
      color: theme.palette.text.primary,
      marginBottom: theme.spacing(1)
    },
    '& p': {
      marginBottom: theme.spacing(1),
      lineHeight: 1.6
    },
    '& table': {
      width: '100%',
      borderCollapse: 'collapse',
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(2),
      backgroundColor: 'white',
      borderRadius: theme.spacing(1),
      overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    },
    '& th': {
      backgroundColor: theme.palette.primary.main,
      color: 'white',
      padding: theme.spacing(1),
      textAlign: 'left',
      fontWeight: 600,
      fontSize: '0.875rem'
    },
    '& td': {
      padding: theme.spacing(1),
      borderBottom: `1px solid ${theme.palette.grey[200]}`,
      fontSize: '0.875rem'
    }
  }));

  return (
    <Fade in={true} timeout={500}>
      <Paper 
        elevation={0}
        sx={{ 
          border: '1px solid',
          borderColor: 'grey.200',
          borderRadius: 3,
          overflow: 'hidden'
        }}
      >
        <Box sx={{ 
          p: 3, 
          bgcolor: 'primary.50',
          borderBottom: '1px solid',
          borderColor: 'grey.200'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Chip
              icon={<AutoAwesomeIcon />}
              label="AI 正在生成测试用例"
              color="primary"
              variant="filled"
              sx={{
                fontWeight: 600,
                animation: `${pulse} 2s ease-in-out infinite`
              }}
            />
          </Box>
          <StyledLinearProgress />
        </Box>

        <Box
          ref={outputRef}
          sx={{
            backgroundColor: 'grey.50',
            p: 3,
            minHeight: '300px',
            maxHeight: '500px',
            overflowY: 'auto',
            wordBreak: 'break-word'
          }}
        >
          {content ? (
            <StyledMarkdown>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </StyledMarkdown>
          ) : (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '200px',
              color: 'text.secondary'
            }}>
              <AutoAwesomeIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                正在分析流程图，准备生成测试用例...
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                请稍候，这可能需要几秒钟时间
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
    </Fade>
  );
};

export default StreamingOutput;
