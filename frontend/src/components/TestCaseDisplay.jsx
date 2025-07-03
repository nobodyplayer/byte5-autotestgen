import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider,
  Card,
  CardContent
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { styled } from '@mui/material/styles';

const TestCaseDisplay = ({ testCases = [], onExportToExcel }) => {
  // 生成Markdown格式的测试用例
  const generateMarkdown = (testCases) => {
    if (!testCases || testCases.length === 0) return '';

    let markdown = '# 生成的测试用例\n\n';

    testCases.forEach((testCase, index) => {
      markdown += `## ${testCase.id || `TC-${index + 1}`}: ${testCase.title}\n\n`;

      if (testCase.priority) {
        markdown += `**优先级:** ${testCase.priority}\n\n`;
      }

      markdown += `**描述:** ${testCase.description}\n\n`;

      if (testCase.preconditions) {
        markdown += `**前置条件:** ${testCase.preconditions}\n\n`;
      }

      markdown += `### 测试步骤\n\n`;
      markdown += `| # | 步骤描述 | 预期结果 |\n`;
      markdown += `| --- | --- | --- |\n`;

      testCase.steps.forEach(step => {
        markdown += `| ${step.step_number} | ${step.description} | ${step.expected_result} |\n`;
      });

      markdown += '\n\n';
    });

    return markdown;
  };

  const StyledMarkdown = styled(Box)(({ theme }) => ({
    '& h1': {
      fontSize: '1.75rem',
      fontWeight: 700,
      color: theme.palette.text.primary,
      marginBottom: theme.spacing(3),
      borderBottom: `2px solid ${theme.palette.primary.main}`,
      paddingBottom: theme.spacing(1)
    },
    '& h2': {
      fontSize: '1.25rem',
      fontWeight: 600,
      color: theme.palette.text.primary,
      marginTop: theme.spacing(4),
      marginBottom: theme.spacing(2),
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing(1)
    },
    '& h3': {
      fontSize: '1.1rem',
      fontWeight: 600,
      color: theme.palette.primary.main,
      marginTop: theme.spacing(3),
      marginBottom: theme.spacing(1.5)
    },
    '& p': {
      marginBottom: theme.spacing(1.5),
      lineHeight: 1.6
    },
    '& table': {
      width: '100%',
      borderCollapse: 'collapse',
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(3),
      backgroundColor: 'white',
      borderRadius: theme.spacing(1),
      overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    },
    '& th': {
      backgroundColor: theme.palette.primary.main,
      color: 'white',
      padding: theme.spacing(1.5),
      textAlign: 'left',
      fontWeight: 600,
      fontSize: '0.875rem'
    },
    '& td': {
      padding: theme.spacing(1.5),
      borderBottom: `1px solid ${theme.palette.grey[200]}`,
      fontSize: '0.875rem',
      lineHeight: 1.5
    },
    '& tr:hover td': {
      backgroundColor: theme.palette.grey[50]
    },
    '& strong': {
      fontWeight: 600,
      color: theme.palette.text.primary
    }
  }));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 2, 
        mb: 3,
        p: 2,
        bgcolor: 'success.50',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'success.200'
      }}>
        <CheckCircleIcon sx={{ color: 'success.main' }} />
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'success.dark' }}>
            测试用例生成完成
          </Typography>
          <Typography variant="body2" color="text.secondary">
            共生成 {testCases.length} 个高质量测试用例
          </Typography>
        </Box>
      </Box>

      <Paper 
        elevation={0}
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          bgcolor: 'grey.50',
          border: '1px solid',
          borderColor: 'grey.200',
          borderRadius: 2
        }}
      >
        <StyledMarkdown sx={{ p: 4 }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {generateMarkdown(testCases)}
          </ReactMarkdown>
        </StyledMarkdown>
      </Paper>
    </Box>
  );
};

export default TestCaseDisplay;
