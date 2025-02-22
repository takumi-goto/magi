"use client";

import Sidebar from "./Sidebar";

export default function BaseLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", width: "100%", height: "100vh" }}>
      {/* Sidebar は常に表示 */}
      <div style={{ backgroundColor: "#f5f5f5", padding: "16px" }}>
        <Sidebar />
      </div>

      {/* メインコンテンツエリア */}
			<div style={{ flexGrow: 1, padding: "20px", overflowY: "auto" }}>
				{children}
			</div>
    </div>
  );
}
