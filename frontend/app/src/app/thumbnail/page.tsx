"use client";

import ThumbnailAnalyzer from "../components/ui/thumbnailAnalyzer/ThumbnailAnalyzer";
import { Container } from '@mantine/core';

export default function ThumbnailPage() {
  const props = {
    h: 50,
    mt: 'xl',
  };
  return (
    <Container fluid {...props}>
      <ThumbnailAnalyzer />
    </Container>
  );
}
