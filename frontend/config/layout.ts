export const LAYOUT_CONFIG = {
  sidebar: {
    width: "256px", // 16rem (w-64)
    collapsedWidth: "80px", // 5rem (w-20)
  },
  topbar: {
    height: "64px", // 4rem (h-16)
  },
  content: {
    padding: "1.5rem", // p-6
    mobilePadding: "1rem", // p-4
  },
  breakpoints: {
    md: 768,
    lg: 1024,
    xl: 1280,
  },
} as const;
