import * as React from "react";

export const VisuallyHidden = ({ children }: { children: React.ReactNode }) => {
  return (
    <span
      className="absolute w-px h-px p-0 -m-px overflow-hidden whitespace-nowrap border-0"
      style={{
        clip: "rect(0, 0, 0, 0)",
      }}
    >
      {children}
    </span>
  );
};
