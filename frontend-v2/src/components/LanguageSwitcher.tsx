import { useTranslation } from "react-i18next";
import { GlobalOutlined } from "@ant-design/icons";
import { Dropdown } from "antd";

const LANGUAGES = [
  { key: "zh-CN", label: "简体中文" },
  { key: "en-US", label: "English" },
];

export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const items = LANGUAGES.map((lang) => ({
    key: lang.key,
    label: lang.label,
  }));

  return (
    <Dropdown
      menu={{
        items,
        selectedKeys: [i18n.language],
        onClick: ({ key }) => i18n.changeLanguage(key),
      }}
      trigger={["click"]}
    >
      <GlobalOutlined style={{ cursor: "pointer", fontSize: 18 }} />
    </Dropdown>
  );
}
