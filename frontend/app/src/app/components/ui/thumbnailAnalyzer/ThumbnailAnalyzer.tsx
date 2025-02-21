import { useState } from "react";

export default function ThumbnailAnalyzer() {
  const [thumbnailUrl, setThumbnailUrl] = useState("");
  const [thumbnailResult, setThumbnailResult] = useState<string | null>(null);
  const [imageData, setImageData] = useState<string | null>(null);

  const analyzeThumbnail = async () => {
    if (!thumbnailUrl) return;

    try {
      const response = await fetch(`/api/analyze-thumbnail?url=${encodeURIComponent(thumbnailUrl)}`);
      const data = await response.json();

      setThumbnailResult(data.result);
      setImageData(data.image);
    } catch (error) {
      console.error("サムネイル解析エラー:", error);
      setThumbnailResult("解析に失敗しました");
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">サムネイル縦長判定</h2>
      <input className="border p-2 w-full" type="text" placeholder="YouTubeサムネイルのURLを入力..." value={thumbnailUrl} onChange={(e) => setThumbnailUrl(e.target.value)} />
      <button onClick={analyzeThumbnail} className="bg-blue-500 text-white px-4 py-2 rounded mt-2">解析開始</button>
      {thumbnailResult && <p>解析結果: {thumbnailResult}</p>}
      {imageData && <img src={imageData} alt="エッジ検出画像" className="mt-2 w-full" />}
    </div>
  );
}
