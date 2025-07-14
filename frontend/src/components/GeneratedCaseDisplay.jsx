import React, { useState, useMemo } from 'react';
import {
    Paper, Typography, Box, Chip, Card, CardContent, Button,
    Dialog, DialogActions, DialogContent, DialogTitle, TextField,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import {
    EditNote as ReviseIcon,
    Autorenew as ReconstructIcon,
    ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';

// 优先级与颜色、排序值的映射
const priorityMap = {
    'P0': { label: 'P0 - 阻塞性', color: '#d32f2f', bgColor: '#ffebee', sortOrder: 0 },
    'P1': { label: 'P1 - 严重', color: '#e65100', bgColor: '#fff3e0', sortOrder: 1 },
    'P2': { label: 'P2 - 主要', color: '#f57c00', bgColor: '#fff8e1', sortOrder: 2 },
    'P3': { label: 'P3 - 次要', color: '#1976d2', bgColor: '#e3f2fd', sortOrder: 3 },
    'P4': { label: 'P4 - 建议', color: '#616161', bgColor: '#f5f5f5', sortOrder: 4 },
    '默认': { label: '中', color: '#f57c00', bgColor: '#fff8e1', sortOrder: 2 }
};

// 用例状态与颜色映射
const statusMap = {
    'Accepted': { label: '已接受', color: '#2e7d32', bgColor: '#e8f5e9' },
    'Reconstructing': { label: '待重构', color: '#d32f2f', bgColor: '#ffebee' }
};


const GeneratedCasesDisplay = ({ generatedCases = [], onStartReconstruction, onUpdateCase }) => {
    // --- 状态管理 ---
    const [reconstructionDialogOpen, setReconstructionDialogOpen] = useState(false);
    const [currentTargetCase, setCurrentTargetCase] = useState(null);
    const [reconstructionFeedback, setReconstructionFeedback] = useState('');

    // --- 数据处理 ---
    // 使用 useMemo 进行排序和分组，只有在 generatedCases 变化时才重新计算
    const groupedAndSortedCases = useMemo(() => {
        if (!generatedCases || generatedCases.length === 0) return {};

        // 1. 排序：按优先级从高到低
        const sortedCases = [...generatedCases].sort((a, b) => {
            const priorityA = priorityMap[a.priority]?.sortOrder ?? 99;
            const priorityB = priorityMap[b.priority]?.sortOrder ?? 99;
            return priorityA - priorityB;
        });

        // 2. 分组：按功能模块
        return sortedCases.reduce((acc, testCase) => {
            const module = testCase.function || '未分类功能';
            if (!acc[module]) {
                acc[module] = [];
            }
            acc[module].push(testCase);
            return acc;
        }, {});
    }, [generatedCases]);

    // --- 事件处理 ---
    const handleOpenReconstructionDialog = (testCase) => {
        setCurrentTargetCase(testCase);
        setReconstructionFeedback(''); // 清空上一次的反馈
        setReconstructionDialogOpen(true);
    };

    const handleCloseReconstructionDialog = () => {
        setReconstructionDialogOpen(false);
        setCurrentTargetCase(null);
    };

    const handleSubmitReconstructionFeedback = () => {
        if (currentTargetCase && reconstructionFeedback) {
            // 调用从父组件传入的回调函数，来更新App的顶层状态
            onUpdateCase(currentTargetCase.id, {
                status: 'Reconstructing',
                feedback: reconstructionFeedback,
            });
        }
        handleCloseReconstructionDialog();
    };

    // --- 渲染 ---
    return (
        <Box sx={{ width: '100%' }}>
            {/* 遍历每个功能模块来渲染手风琴式折叠面板 */}
            {Object.entries(groupedAndSortedCases).map(([moduleName, casesInModule]) => (
                <Accordion key={moduleName} defaultExpanded sx={{ mb: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>{moduleName}</Typography>
                            <Chip label={`${casesInModule.length} 个用例`} color="primary" variant="outlined" size="small" />
                        </Box>
                    </AccordionSummary>
                    <AccordionDetails sx={{ display: 'flex', flexDirection: 'column', gap: 2, bgcolor: 'grey.50' }}>
                        {/* 遍历模块下的每个测试用例，渲染成卡片 */}
                        {casesInModule.map((testCase) => {
                            const priorityInfo = priorityMap[testCase.priority] || priorityMap['默认'];
                            const statusInfo = statusMap[testCase.status] || { label: '未知', color: 'grey', bgColor: '#e0e0e0' };

                            return (
                                <Card key={testCase.id} variant="outlined" sx={{ borderLeft: `5px solid ${priorityInfo.color}` }}>
                                    <CardContent>
                                        {/* 头部：ID, 标题, 优先级和状态 */}
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
                                            <Typography variant="h6" component="div" sx={{ fontWeight: 500 }}>
                                                {testCase.id}: {testCase.title}
                                            </Typography>
                                            <Box sx={{ display: 'flex', gap: 1 }}>
                                                <Chip label={priorityInfo.label} size="small" sx={{ bgcolor: priorityInfo.bgColor, color: priorityInfo.color, fontWeight: 'bold' }} />
                                                <Chip label={statusInfo.label} size="small" sx={{ bgcolor: statusInfo.bgColor, color: statusInfo.color }} />
                                            </Box>
                                        </Box>

                                        {/* 详情：前置条件 */}
                                        {testCase.prerequisite && (
                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
                                                <strong>前置条件:</strong> {testCase.prerequisite}
                                            </Typography>
                                        )}

                                        {/* 核心：步骤表格 */}
                                        <TableContainer component={Paper} elevation={0} variant="outlined">
                                            <Table size="small">
                                                <TableHead sx={{ bgcolor: 'grey.100' }}>
                                                    <TableRow>
                                                        <TableCell sx={{ width: '5%', fontWeight: 'bold' }}>#</TableCell>
                                                        <TableCell sx={{ fontWeight: 'bold' }}>操作步骤</TableCell>
                                                        <TableCell sx={{ fontWeight: 'bold' }}>预期结果</TableCell>
                                                    </TableRow>
                                                </TableHead>
                                                <TableBody>
                                                    {testCase.steps.map((step, index) => (
                                                        <TableRow key={index}>
                                                            <TableCell>{step.step_number}</TableCell>
                                                            <TableCell sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{step.description}</TableCell>
                                                            <TableCell sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{step.expected_result}</TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </TableContainer>

                                        {/* 底部：操作按钮 */}
                                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                                            <Button
                                                variant="outlined"
                                                size="small"
                                                startIcon={<ReviseIcon />}
                                                onClick={() => handleOpenReconstructionDialog(testCase)}
                                                disabled={testCase.status === 'Reconstructing'}
                                            >
                                                请求修订
                                            </Button>
                                        </Box>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </AccordionDetails>
                </Accordion>
            ))}

            {/* 全局操作按钮 */}
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <Button
                    variant="contained"
                    size="large"
                    startIcon={<ReconstructIcon />}
                    onClick={() => onStartReconstruction()}
                >
                    开始重构所有“待重构”用例
                </Button>
            </Box>

            {/* 修订意见输入对话框 */}
            <Dialog open={reconstructionDialogOpen} onClose={handleCloseReconstructionDialog} fullWidth maxWidth="sm">
                <DialogTitle>请求修订: {currentTargetCase?.id}</DialogTitle>
                <DialogContent>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                        <strong>测试点:</strong> {currentTargetCase?.testPoint}
                    </Typography>
                    <TextField
                        autoFocus
                        margin="dense"
                        id="feedback"
                        label="请输入您的修订意见或反馈"
                        type="text"
                        fullWidth
                        multiline
                        rows={4}
                        value={reconstructionFeedback}
                        onChange={(e) => setReconstructionFeedback(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseReconstructionDialog}>取消</Button>
                    <Button onClick={handleSubmitReconstructionFeedback} variant="contained">提交修订请求</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default GeneratedCasesDisplay;