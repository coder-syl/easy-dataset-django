'use client';

import React from 'react';
import { Menu, MenuItem, ListItemIcon, ListItemText, Divider } from '@mui/material';
import { useTranslation } from 'react-i18next';
import Link from 'next/link';
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import ImageIcon from '@mui/icons-material/Image';
import DatasetOutlinedIcon from '@mui/icons-material/DatasetOutlined';
import ChatIcon from '@mui/icons-material/Chat';
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import StorageIcon from '@mui/icons-material/Storage';
import * as styles from './styles';

/**
 * DesktopMenus 组件
 * 桌面端悬停菜单，包含数据源、数据集管理、更多三个菜单
 */
export default function DesktopMenus({ theme, menuState, isMenuOpen, handleMenuClose, currentProject }) {
  const { t } = useTranslation();

  return (
    <>
      {/* 数据源菜单 */}
      <Menu
        anchorEl={menuState.anchorEl}
        open={isMenuOpen('source')}
        onClose={handleMenuClose}
        aria-label={t('common.dataSource', 'Data source menu')}
        PaperProps={{
          elevation: 8,
          sx: styles.getMenuPaperStyles(theme),
          onMouseLeave: handleMenuClose
        }}
        transformOrigin={{ horizontal: 'center', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
        MenuListProps={{
          dense: false,
          onMouseLeave: handleMenuClose,
          sx: styles.menuListStyles,
          role: 'menu'
        }}
        transitionDuration={200}
      >
        <MenuItem
          component={Link}
          href={`/projects/${currentProject}/text-split`}
          onClick={handleMenuClose}
          role="menuitem"
          sx={styles.getMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.listItemIconStyles}>
            <DescriptionOutlinedIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText primary={t('textSplit.title')} primaryTypographyProps={styles.smallListItemTextStyles} />
        </MenuItem>
        <Divider sx={{ my: 0.75, mx: 1.5 }} />
        <MenuItem
          component={Link}
          href={`/projects/${currentProject}/images`}
          onClick={handleMenuClose}
          role="menuitem"
          sx={styles.getMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.listItemIconStyles}>
            <ImageIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText primary={t('images.title')} primaryTypographyProps={styles.smallListItemTextStyles} />
        </MenuItem>
      </Menu>

      {/* 数据集管理菜单 */}
      <Menu
        anchorEl={menuState.anchorEl}
        open={isMenuOpen('dataset')}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 8,
          sx: styles.getSimpleMenuPaperStyles(theme),
          onMouseLeave: handleMenuClose
        }}
        transformOrigin={{ horizontal: 'center', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
        MenuListProps={{
          dense: true,
          onMouseLeave: handleMenuClose,
          sx: styles.simpleMenuListStyles
        }}
      >
        <MenuItem
          component={Link}
          href={`/projects/${currentProject}/datasets`}
          onClick={handleMenuClose}
          sx={styles.getSimpleMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.smallListItemIconStyles}>
            <DatasetOutlinedIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText
            primary={t('datasets.singleTurn', '单轮问答数据集')}
            primaryTypographyProps={styles.smallListItemTextStyles}
          />
        </MenuItem>
        <Divider sx={{ my: 0.5, mx: 1 }} />
        <MenuItem
          component={Link}
          href={`/projects/${currentProject}/multi-turn`}
          onClick={handleMenuClose}
          sx={styles.getSimpleMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.smallListItemIconStyles}>
            <ChatIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText
            primary={t('datasets.multiTurn', '多轮对话数据集')}
            primaryTypographyProps={styles.smallListItemTextStyles}
          />
        </MenuItem>
        <Divider sx={{ my: 0.5, mx: 1 }} />
        <MenuItem
          component={Link}
          href={`/projects/${currentProject}/image-datasets`}
          onClick={handleMenuClose}
          sx={styles.getSimpleMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.smallListItemIconStyles}>
            <ImageIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText
            primary={t('datasets.imageQA', '图片问答数据集')}
            primaryTypographyProps={styles.smallListItemTextStyles}
          />
        </MenuItem>
      </Menu>

      {/* 更多菜单 */}
      <Menu
        anchorEl={menuState.anchorEl}
        open={isMenuOpen('more')}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 8,
          sx: styles.getSimpleMenuPaperStyles(theme),
          onMouseLeave: handleMenuClose
        }}
        transformOrigin={{ horizontal: 'center', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
        MenuListProps={{
          dense: true,
          onMouseLeave: handleMenuClose,
          sx: styles.simpleMenuListStyles
        }}
      >
        <MenuItem
          component={Link}
          href={`/projects/${currentProject}/settings`}
          onClick={handleMenuClose}
          sx={styles.getSimpleMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.smallListItemIconStyles}>
            <SettingsOutlinedIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText primary={t('settings.title')} primaryTypographyProps={styles.smallListItemTextStyles} />
        </MenuItem>
        <Divider sx={{ my: 0.5, mx: 1 }} />
        <MenuItem
          component={Link}
          href={`/projects/${currentProject}/playground`}
          onClick={handleMenuClose}
          sx={styles.getSimpleMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.smallListItemIconStyles}>
            <ScienceOutlinedIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText primary={t('playground.title')} primaryTypographyProps={styles.smallListItemTextStyles} />
        </MenuItem>
        <Divider sx={{ my: 0.5, mx: 1 }} />
        <MenuItem
          component={Link}
          href="/dataset-square"
          onClick={handleMenuClose}
          sx={styles.getSimpleMenuItemStyles(theme)}
        >
          <ListItemIcon sx={styles.smallListItemIconStyles}>
            <StorageIcon fontSize="small" sx={styles.getPrimaryIconColorStyles(theme)} />
          </ListItemIcon>
          <ListItemText primary={t('datasetSquare.title')} primaryTypographyProps={styles.smallListItemTextStyles} />
        </MenuItem>
      </Menu>
    </>
  );
}
