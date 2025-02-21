"use client";

import ThumbnailAnalyzer from "../components/ui/thumbnailAnalyzer/ThumbnailAnalyzer";

export default function ThumbnailPage() {
  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">サムネイル判定</h1>
      <ThumbnailAnalyzer />
    </div>
  );
}
