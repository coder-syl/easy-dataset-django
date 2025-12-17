'use client';

import { Box, Typography, Chip, Tooltip, alpha, Paper } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';

/**
 * 多轮对话元数据展示组件
 */
export default function ConversationMetadata({ conversation }) {
  const { t } = useTranslation();
  const theme = useTheme();

  if (!conversation) return null;

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 1 }}>
        {t('datasets.metadata')}
      </Typography>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip label={`${t('datasets.modelUsed')}: ${conversation.model}`} variant="outlined" size="small" />

        {conversation.scenario && (
          <Chip
            label={`${t('datasets.conversationScenario')}: ${conversation.scenario}`}
            color="primary"
            variant="outlined"
            size="small"
          />
        )}

        <Chip
          label={`${t('datasets.conversationRounds')}: ${conversation.turn_count}/${conversation.max_turns}`}
          variant="outlined"
          size="small"
        />

        {conversation.role_a && (
          <Chip
            label={`${t('settings.multiTurnRoleA')}: ${conversation.role_a}`}
            variant="outlined"
            color="info"
            size="small"
          />
        )}

        {conversation.role_b && (
          <Chip
            label={`${t('settings.multiTurnRoleB')}: ${conversation.role_b}`}
            variant="outlined"
            color="secondary"
            size="small"
          />
        )}

        {conversation.create_at && (
          <Chip
            label={`${t('datasets.createdAt')}: ${new Date(conversation.create_at).toLocaleDateString()}`}
            variant="outlined"
            size="small"
          />
        )}

        {conversation.confirmed && (
          <Chip
            label={t('datasets.confirmed')}
            size="small"
            sx={{
              backgroundColor: alpha(theme.palette.success.main, 0.1),
              color: theme.palette.success.dark,
              fontWeight: 'medium'
            }}
          />
        )}
      </Box>
    </Paper>
  );
}
