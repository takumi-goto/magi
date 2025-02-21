"use client";

import Magi from "../components/ui/magi/Magi";
import { Container } from '@mantine/core';

export default function MagiPage() {
  const props = {
    h: 50,
    mt: 'xl',
  };
  return (
    <Container fluid {...props}>
      <Magi />
    </Container>
  );
}
