import React from "react";

interface Props {
  height?: number;
}

export const Skeleton: React.FC<Props> = ({ height = 160 }) => (
  <div
    style={{
      height,
      borderRadius: 4,
      background:
        "linear-gradient(90deg, #EAECEF 25%, #F5F6F8 50%, #EAECEF 75%)",
      backgroundSize: "400% 100%",
      animation: "shimmer 1.5s infinite",
    }}
  />
);
