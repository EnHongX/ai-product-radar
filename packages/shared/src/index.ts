export const companyTypes = [
  "ai_lab",
  "big_tech",
  "cloud_provider",
  "startup",
  "open_source",
  "developer_tool",
  "hardware",
  "enterprise_saas"
] as const;

export const sourceTypes = ["rss", "blog", "newsroom", "changelog", "github_release", "sitemap", "html", "app_store"] as const;

export const parseStrategies = ["rss", "sitemap", "static_html", "dynamic_html", "github_api", "custom"] as const;

export const reviewStatuses = ["pending", "approved", "rejected", "duplicate"] as const;

export const productCategories = ["model", "app", "api", "agent", "plugin", "developer_tool", "platform", "hardware"] as const;

export const supportedPlatforms = [
  "web",
  "ios",
  "android",
  "macos",
  "windows",
  "linux",
  "api",
  "chrome_extension",
  "slack",
  "excel",
  "figma",
  "github",
  "vscode"
] as const;
