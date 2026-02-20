/**
 * Addverb Brand Design Tokens
 * Single source of truth for all colors used across the dashboard.
 */
export const R = {
  // Primary brand
  red: "#E8001C",
  redDark: "#B8001A",
  redLight: "#FFF0F1",

  // Neutrals
  black: "#111214",
  darkGray: "#1E2125",
  midGray: "#3A3F47",

  // Text
  textPrimary: "#111214",
  textSecondary: "#5A6170",
  textMuted: "#9BA3AE",

  // Borders & surfaces
  border: "#E4E7EB",
  borderLight: "#F0F2F4",
  bg: "#F7F8FA",
  white: "#FFFFFF",

  // Semantic
  green: "#00A651",
  greenLight: "#E6F7EF",
  amber: "#F59E0B",
  amberLight: "#FEF3C7",
} as const;

export type BrandTokens = typeof R;
