"use client";

import { IconHome2, IconGauge } from '@tabler/icons-react';
import { NavLink } from '@mantine/core';
import { useRouter, usePathname } from "next/navigation";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const active = pathname.includes("/thumbnail") ? "thumbnail" : "magi";

  return (
    <div style={{ width: 250, padding: '16px', backgroundColor: '#f5f5f5', height: '100vh' }}>
      <NavLink
        label="Magi"
        leftSection={<IconHome2 size={16} stroke={1.5} />}
        active={active === "magi"}
        onClick={() => router.push("/magi")}
        variant="filled"
      />

      <NavLink
        label="サムネイル"
        leftSection={<IconGauge size={16} stroke={1.5} />}
        active={active === "thumbnail"}
        onClick={() => router.push("/thumbnail")}
        variant="filled"
      />
    </div>
  );
}
