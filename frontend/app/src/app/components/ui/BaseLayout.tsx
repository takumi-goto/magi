"use client"; // ✅ クライアントコンポーネント

import { Container } from "@mantine/core";
import Sidebar from "./Sidebar";

export default function BaseLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", width: "100vw", height: "100vh" }}>
      {/* ✅ Sidebar は常に表示 */}
      <div style={{ width: "250px", backgroundColor: "#f5f5f5", padding: "16px" }}>
        <Sidebar />
      </div>

      {/* ✅ メインコンテンツエリア */}
      <div style={{ flexGrow: 1, padding: "20px", overflowY: "auto" }}>
        <Container>{children}</Container>
      </div>
    </div>
  );
}
