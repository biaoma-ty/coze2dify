import { useMemo } from "react";
import type { ReactNode } from "react";
import {
  DashboardOutlined,
  ExperimentOutlined,
  GlobalOutlined,
  HistoryOutlined,
  SettingOutlined,
  SwapOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import { ProLayout } from "@ant-design/pro-components";
import { ConfigProvider, Button, Space, Tag } from "antd";
import enUS from "antd/lib/locale/en_US";
import zhCN from "antd/lib/locale/zh_CN";
import { Link, Outlet, useLocation } from "@umijs/max";
import { useTranslation } from "react-i18next";
import { usePlatformStore } from "../store/platformStore";
import "../i18n";
import "../styles.css";

type MenuItem = {
  icon: ReactNode;
  key: string;
  name: string;
  path: string;
};

export default function RootLayout() {
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const devModeEnabled = usePlatformStore((state) => state.devModeEnabled);

  const menuItems = useMemo<MenuItem[]>(
    () => [
      {
        key: "dashboard",
        path: "/",
        name: t("nav.dashboard"),
        icon: <DashboardOutlined />,
      },
      {
        key: "migrate",
        path: "/migrate",
        name: t("nav.migrate"),
        icon: <SwapOutlined />,
      },
      {
        key: "sync",
        path: "/sync",
        name: t("nav.sync"),
        icon: <SyncOutlined />,
      },
      {
        key: "history",
        path: "/history",
        name: t("nav.history"),
        icon: <HistoryOutlined />,
      },
      {
        key: "workbench",
        path: "/workbench",
        name: t("nav.workbench"),
        icon: <ExperimentOutlined />,
      },
      {
        key: "settings",
        path: "/settings",
        name: t("nav.settings"),
        icon: <SettingOutlined />,
      },
    ],
    [t],
  );

  const locale = i18n.language === "zh" ? zhCN : enUS;
  const isWorkbenchRoute = location.pathname.startsWith("/workbench");

  const toggleLanguage = () => {
    const nextLanguage = i18n.language === "zh" ? "en" : "zh";
    void i18n.changeLanguage(nextLanguage);
    localStorage.setItem("c2d-lang", nextLanguage);
  };

  const shellContent = isWorkbenchRoute ? (
    <Outlet />
  ) : (
    <ProLayout
      actionsRender={() => [
        <Space key="app-actions" size={12}>
          {devModeEnabled && (
            <Tag className="app-shell__dev-tag" color="gold">
              DEV MODE
            </Tag>
          )}
          <Button
            className="app-shell__lang-switch"
            icon={<GlobalOutlined />}
            onClick={toggleLanguage}
            type="text"
          >
            {i18n.language === "zh" ? "EN" : "ZH"}
          </Button>
          <Tag className="app-shell__version-tag">v0.2.0</Tag>
        </Space>,
      ]}
      avatarProps={false}
      breadcrumbRender={false}
      fixSiderbar
      fixedHeader
      headerTitleRender={() => (
        <Link className="app-shell__brand" to="/">
          <span className="app-shell__brand-mark">C2D</span>
          <span className="app-shell__brand-name">
            coze<span>2</span>dify
          </span>
        </Link>
      )}
      layout="mix"
      location={{ pathname: location.pathname }}
      logo={false}
      menuHeaderRender={() => (
        <Link className="app-shell__brand" to="/">
          <span className="app-shell__brand-mark">C2D</span>
          <span className="app-shell__brand-name">
            coze<span>2</span>dify
          </span>
        </Link>
      )}
      menuItemRender={(item, dom) =>
        item.path ? (
          <Link to={item.path} style={{ textDecoration: "none" }}>
            {dom}
          </Link>
        ) : (
          dom
        )
      }
      navTheme="realDark"
      pageTitleRender={false}
      route={{ routes: menuItems }}
      siderWidth={228}
      splitMenus={false}
    >
      <main className="app-shell__content">
        <div className="app-shell__content-inner">
          <Outlet />
        </div>
      </main>
    </ProLayout>
  );

  return <ConfigProvider locale={locale}>{shellContent}</ConfigProvider>;
}
