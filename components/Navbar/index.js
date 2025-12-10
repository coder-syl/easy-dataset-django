'use client';

import React, { useState } from 'react';
import { AppBar, Toolbar, Box, IconButton, useTheme as useMuiTheme, Tooltip, useMediaQuery } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { usePathname } from 'next/navigation';
import { useTheme } from 'next-themes';
import MenuIcon from '@mui/icons-material/Menu';

// 样式
import * as styles from './styles';

// 子组件
import Logo from './Logo';
import ActionButtons from './ActionButtons';
import NavigationTabs from './NavigationTabs';
import MobileDrawer from './MobileDrawer';
import DesktopMenus from './DesktopMenus';
import ContextBar from './ContextBar';

export default function Navbar({ projects = [], currentProject }) {
  const { t, i18n } = useTranslation();
  const pathname = usePathname();
  const theme = useMuiTheme();
  const { resolvedTheme, setTheme } = useTheme();
  const isProjectDetail = pathname.includes('/projects/') && pathname.split('/').length > 3;

  // 检测移动设备
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));

  // 移动端抽屉状态
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [expandedMenu, setExpandedMenu] = useState(null);

  // 桌面端菜单状态
  const [menuState, setMenuState] = useState({ anchorEl: null, menuType: null });

  // ContextBar 悬浮状态
  const [contextBarHovered, setContextBarHovered] = useState(false);

  const handleMenuOpen = (event, menuType) => {
    setMenuState({ anchorEl: event.currentTarget, menuType });
  };

  const handleMenuClose = () => {
    setMenuState({ anchorEl: null, menuType: null });
  };

  const isMenuOpen = menuType => menuState.menuType === menuType;

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
    setExpandedMenu(null);
  };

  const toggleMobileSubmenu = menuType => {
    setExpandedMenu(expandedMenu === menuType ? null : menuType);
  };

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <>
      <AppBar
        component="nav"
        position="sticky"
        elevation={0}
        color={theme.palette.mode === 'dark' ? 'transparent' : 'primary'}
        sx={styles.getAppBarStyles(theme)}
        style={{ borderRadius: 0, zIndex: 1200 }}
        role="navigation"
        aria-label={t('common.mainNavigation', 'Main navigation')}
      >
        <Toolbar sx={styles.toolbarStyles}>
          {/* 左侧: 汉堡菜单(移动端) + Logo */}
          <Box sx={styles.logoContainerStyles} onMouseEnter={() => isProjectDetail && setContextBarHovered(true)}>
            {/* 汉堡菜单按钮 */}
            {isProjectDetail && isMobile && (
              <Tooltip title={t('common.menu', 'Menu')} placement="bottom">
                <IconButton
                  onClick={toggleDrawer}
                  size="medium"
                  aria-label={t('common.openMenu', 'Open navigation menu')}
                  aria-expanded={drawerOpen}
                  aria-controls="mobile-navigation-drawer"
                  sx={styles.getHamburgerButtonStyles(theme)}
                >
                  <MenuIcon />
                </IconButton>
              </Tooltip>
            )}

            {/* Logo 组件 */}
            <Logo theme={theme} />
          </Box>

          {/* 中间导航 - 仅桌面端 */}
          {isProjectDetail && !isMobile && (
            <NavigationTabs
              theme={theme}
              pathname={pathname}
              currentProject={currentProject}
              handleMenuOpen={handleMenuOpen}
              handleMenuClose={handleMenuClose}
            />
          )}

          {/* 右侧操作区 */}
          <ActionButtons
            theme={theme}
            resolvedTheme={resolvedTheme}
            toggleTheme={toggleTheme}
            isProjectDetail={isProjectDetail}
            currentProject={currentProject}
          />
        </Toolbar>
      </AppBar>

      {/* ContextBar - 在 Logo 或 ContextBar 悬浮时展示 */}
      {isProjectDetail && contextBarHovered && (
        <Box onMouseLeave={() => setContextBarHovered(false)}>
          <ContextBar
            projects={projects}
            currentProjectId={currentProject}
            onMouseLeave={() => setContextBarHovered(false)}
          />
        </Box>
      )}

      {/* 移动端抽屉组件 */}
      <MobileDrawer
        theme={theme}
        drawerOpen={drawerOpen}
        toggleDrawer={toggleDrawer}
        expandedMenu={expandedMenu}
        toggleMobileSubmenu={toggleMobileSubmenu}
        currentProject={currentProject}
      />

      {/* 桌面端菜单组件 */}
      <DesktopMenus
        theme={theme}
        menuState={menuState}
        isMenuOpen={isMenuOpen}
        handleMenuClose={handleMenuClose}
        currentProject={currentProject}
      />
    </>
  );
}
