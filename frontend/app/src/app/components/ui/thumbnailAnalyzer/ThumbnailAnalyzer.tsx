import { useState } from "react";
import {
  Input, Button, Space, Group, Title, Box, Stack, Card, Image, Text, Loader, Paper, SimpleGrid
} from '@mantine/core';

export default function ThumbnailAnalyzer() {
  const [youtubeVideoId, setYoutubeVideoId] = useState("");
  const [thumbnailResult, setThumbnailResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const analyzeThumbnail = async () => {
    if (!youtubeVideoId) return;

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8001/api/analyze-thumbnail?video_id=${encodeURIComponent(youtubeVideoId)}`);
      const data = await response.json();

      setThumbnailResult(data);
    } catch (error) {
      console.error("サムネイル解析エラー:", error);
      setThumbnailResult({ error: "解析に失敗しました" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <Stack align="center" justify="center" gap="lg">
        <Title order={1}>サムネイル縦長判定</Title>
        <Box style={{ overflow: 'hidden' }}>
          <Group justify="center">
            <Input
              type="text"
              placeholder="YouTube動画IDを入力..."
              value={youtubeVideoId}
              onChange={(e) => setYoutubeVideoId(e.target.value)}
              size="md"
              w={300}
            />
            <Space />
            <Button
              variant="filled"
              color="teal"
              onClick={analyzeThumbnail}
              disabled={!youtubeVideoId.trim()}
              size="md"
            >
              {loading ? <Loader size="sm" color="white" /> : "送信"}
            </Button>
          </Group>
        </Box>
      </Stack>

      {thumbnailResult && (
        <Paper withBorder shadow="sm" p="md" mt="lg">
          <Title order={3}>解析結果</Title>
          {thumbnailResult.error ? (
            <Text color="red">{thumbnailResult.error}</Text>
          ) : (
            <>
              <Text>動画の幅: {thumbnailResult.width}px</Text>
              <Text>動画の高さ: {thumbnailResult.height}px</Text>
              <Text>縦線の高さ: {thumbnailResult.vertical_height}px</Text>
              <Text>縦線の間隔: {thumbnailResult.vertical_width}px</Text>
              <Text fw={700} color={thumbnailResult.orientation === "縦長" ? "blue" : "green"}>
                判定結果: {thumbnailResult.orientation}
              </Text>
            </>
          )}
        </Paper>
      )}

{thumbnailResult && thumbnailResult.thumbnail_url && (
  <Card shadow="sm" p="lg" radius="md" withBorder mt="md">
    <Text ta="center" fw={700} mb="sm">サムネイル解析結果</Text>

    <SimpleGrid cols={2} spacing="sm">
      <Card.Section>
        <Image
          src={thumbnailResult.thumbnail_url}
          alt="サムネイル画像"
          width={640}
          height={480}
          fit="contain"
        />
        <Text ta="center" size="sm" mt="xs">オリジナル</Text>
      </Card.Section>

      <Card.Section>
        <Image
          src={thumbnailResult.processed_image}
          alt="加工画像"
          width={640}
          height={480}
          fit="contain"
        />
        <Text ta="center" size="sm" mt="xs">加工後</Text>
      </Card.Section>
    </SimpleGrid>
  </Card>
)}
    </div>
  );
}
