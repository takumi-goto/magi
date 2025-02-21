"use client";

import { useEffect, useState, useRef } from "react";
import { PDFDocument, rgb } from "pdf-lib";
import fontkit from "@pdf-lib/fontkit";
import { marked } from "marked";
import WebSocketManager from "../../../utils/WebSocketManager";
import { Textarea, Button, Space, Group, Title, Box, Stack, Radio, Paper, Avatar, Text, ScrollArea } from '@mantine/core';
import { IconDownload } from '@tabler/icons-react';

interface Message {
  sender: string; // 例: "User" | "GPT(3.5)" | "Gemini(2.0)" | "GPTまとめ"
  text: string;
}

export default function Magi() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState("");
  const [analysisType, setAnalysisType] = useState("none");
  const [videoId, setVideoId] = useState("");
  const [channelId, setChannelId] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  /** ✅ メッセージが追加されるたびにスクロール */
  const viewport = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (viewport.current) {
      viewport.current.scrollTo({ top: viewport.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages]); // メッセージが追加されたときに発火

  /** ✅ WebSocket の接続とリスナーを設定 */
  useEffect(() => {
    WebSocketManager.connect("ws://localhost:8001/ws");

    const messageListener = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as Message;
        setMessages((prev) => [...prev, data]);
        setLoading(false);
      } catch (error) {
        console.error("メッセージのパースエラー:", error);
      }
    };

    WebSocketManager.addListener(messageListener);
    setIsConnected(true);

    return () => {
      WebSocketManager.removeListener(messageListener);
    };
  }, []);

  /** ✅ WebSocket のメッセージ送信 */
  const sendMessage = () => {
    if (WebSocketManager.socketInstance && WebSocketManager.isConnected) {
      const payload = {
        topic,
        analysisType: analysisType !== "none" ? analysisType : undefined,
        videoId: analysisType === "comment_analysis" ? videoId : undefined,
        channelId: analysisType === "channel_subscriber_popular_channel" ? channelId : undefined,
      };

      console.log("送信データ:", payload);
      setMessages((prev) => [...prev, { sender: "User", text: topic }]);
      WebSocketManager.socketInstance.send(JSON.stringify(payload));
      setTopic("");
      setLoading(true);
    } else {
      console.warn("WebSocket未接続です");
    }
  };

  /** ✅ メッセージ表示処理 */
  const renderMessage = (msg: Message, index: number) => {
    const isUser = msg.sender === "User";
    const isGemini = msg.sender.includes("Gemini");
    const isGPT = msg.sender.includes("GPT");

    // ✅ 色分け
    const bgColor = isUser ? "blue.6" : isGemini ? "green.6" : isGPT ? "violet.6" : "gray.6";

    return (
      <Group
        key={`${msg.sender}-${msg.text}-${index}`}
        align="flex-start"
        justify={isUser ? "flex-end" : "flex-start"}
        gap="xs"
        style={{ marginBottom: "10px" }}
      >
        {!isUser && (
          <Avatar
            radius="xl"
            src={isGemini ? "/gemini.png" : isGPT ? "/gpt.png" : "/default-avatar.png"}
            size={40}
          />
        )}

        <Paper
          shadow="xs"
          radius="md"
          p="md"
          bg={bgColor}
          style={{
            maxWidth: "70%",
            color: "white",
            wordBreak: "break-word",
            lineHeight: "1.6",
          }}
        >
          <Text size="sm" fw={500}>{msg.sender}</Text>
          <Text size="sm">{msg.text}</Text>
        </Paper>

        {isUser && <Avatar radius="xl" src="/user-avatar.png" size={40} />}
      </Group>
    );
  };

  /** ✅ テキストの自動改行処理（PDF用） */
  const wrapText = (text: string, font: any, fontSize: number, maxWidth: number) => {
    const lines: string[] = [];
    let currentLine = "";

    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      const width = font.widthOfTextAtSize(currentLine + char, fontSize);

      if (width > maxWidth) {
        lines.push(currentLine);
        currentLine = char;
      } else {
        currentLine += char;
      }
    }

    lines.push(currentLine);
    return lines;
  };

	/** ✅ チャット欄をクリアする */
	const clearChat = () => {
		setMessages([]);
	};

  /** ✅ PDF 生成 */
  const generatePDF = async () => {
    const pdfDoc = await PDFDocument.create();
    pdfDoc.registerFontkit(fontkit);

    const fontBytes = await fetch("/fonts/NotoSansJP-VariableFont_wght.ttf").then((res) => res.arrayBuffer());
    const notoSansJP = await pdfDoc.embedFont(fontBytes);

    let page = pdfDoc.addPage([600, 800]);
    const { width, height } = page.getSize();
    let yOffset = height - 50;
    const lineHeight = 16;
    const marginX = 50;
    const maxWidth = width - marginX * 2;

    page.drawText("議論記録", {
      x: marginX,
      y: yOffset,
      size: 20,
      font: notoSansJP,
      color: rgb(0, 0, 0),
    });

    yOffset -= 30;

    const markdownText = messages.filter((msg) => msg.sender === "GPTまとめ").map((msg) => msg.text).join("\n\n");
    const mdHtml = marked.parse(markdownText, { renderer: new marked.Renderer() }) as string;
    const plainText = mdHtml.replace(/<\/?[^>]+(>|$)/g, "");

    const paragraphs = plainText.split("\n");

    paragraphs.forEach((paragraph: string) => {
      const wrappedLines = wrapText(paragraph, notoSansJP, 12, maxWidth);

      wrappedLines.forEach((line) => {
        page.drawText(line, { x: marginX, y: yOffset, size: 12, font: notoSansJP, color: rgb(0, 0, 0) });
        yOffset -= lineHeight;

        if (yOffset < 50) {
          page = pdfDoc.addPage([600, 800]);
          yOffset = height - 30;
        }
      });

      yOffset -= 5;
    });

    const pdfBytes = await pdfDoc.save();
    const blob = new Blob([pdfBytes], { type: "application/pdf" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "議論記録.pdf";
    link.click();
  };

  return (
    <>
      <Stack
        h={300}
        bg="var(--mantine-color-body)"
        align="stretch"
        justify="center"
        gap="lg"
      >
        <Title order={1}>MAG(K)I:||</Title>
        <Space />
        <Box style={{ overflow: 'hidden' }}>
          <Group>
            <Textarea
              placeholder="議題やメッセージを入力..."
              value={topic}
              size="sm"
              w="70%"
              onChange={(event) => setTopic(event.target.value)}
            />
            <Space />
            <Button variant="filled" color="teal" onClick={sendMessage} disabled={!WebSocketManager.isConnected || !topic.trim()}>
              送信
            </Button>
            <Space />
            {/* チャットをクリアボタンを追加 */}
            <Button variant="filled" color="gray" onClick={clearChat} disabled={messages.length === 0}>
              チャット欄をクリア
            </Button>
          </Group>
        </Box>
      </Stack>

      <Stack h={700} bg="var(--mantine-color-body)" align="stretch" justify="center" gap="lg">
        {/* 分析タイプ選択 */}
        <Radio.Group
          value={analysisType} // 選択された値を管理
          onChange={setAnalysisType} // チェックされた時に state 更新
        >
          <Group>
            <Radio label="分析なし" value="none" />
            <Radio label="コメント分析" value="comment_analysis" />
            <Radio label="視聴者人気のチャンネル分析" value="channel_subscriber_popular_channel" />
          </Group>
        </Radio.Group>

        <ScrollArea h={800} viewportRef={viewport} style={{ borderRadius: "8px", backgroundColor: "#f0f0f0", padding: "10px" }}>
          {messages.map((msg, idx) => renderMessage(msg, idx))}
        </ScrollArea>

        {messages.length > 0 && messages[messages.length - 1].sender === "GPTまとめ" && (
          <Button
            variant="filled"
            color="red"
            onClick={generatePDF}
            w="fit-content"
            miw={150}
            rightSection={<IconDownload size={14} />}
          >
            PDFで出力
          </Button>
        )}
      </Stack>

      <p className="mt-2">Status: {WebSocketManager.isConnected ? "Connected" : "Disconnected"}</p>
    </>
  );
}
