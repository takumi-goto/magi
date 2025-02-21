"use client";

import { useEffect, useState, useRef } from "react";
import { PDFDocument, rgb } from "pdf-lib";
import fontkit from "@pdf-lib/fontkit";
import { marked } from "marked";
import WebSocketManager from "../../../utils/WebSocketManager";

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
  useEffect(() => {
    if (messagesEndRef.current) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, 100);
    }
  }, [messages]);

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
    let alignment = "justify-start";
    let bgColor = "bg-blue-200";

    if (msg.sender.includes("Gemini")) {
      alignment = "justify-end";
      bgColor = "bg-green-200";
    } else if (msg.sender === "User") {
      alignment = "justify-center";
      bgColor = "bg-gray-300";
    }

    return (
      <div key={`${msg.sender}-${msg.text}-${index}`} className={`flex mb-2 ${alignment}`}>
        <div className={`p-2 rounded-lg max-w-xs ${bgColor}`}>
          <strong>{msg.sender}:</strong> {msg.text}
        </div>
      </div>
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
    <div className="h-screen flex flex-col p-4">
      <h1 className="text-2xl font-bold mb-4">MAG(K)I波MARI イラストりあす</h1>

      <div className="mt-4 flex space-x-2">
        <input
          className="border p-2 flex-1"
          type="text"
          placeholder="議題やメッセージを入力..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />
        <button onClick={sendMessage} className="bg-blue-500 text-white px-4 py-2 rounded" disabled={!WebSocketManager.isConnected || !topic.trim()}>
          送信
        </button>
				{/* チャットをクリアボタンを追加 */}
				<button onClick={clearChat} className="bg-purple-500 text-white px-4 py-2 rounded mt-2" disabled={messages.length === 0}>
          チャット欄をクリア
        </button>
      </div>

      {/* 分析タイプ選択 */}
      <div className="mt-4">
        <label>
          <input type="radio" value="none" checked={analysisType === "none"} onChange={() => setAnalysisType("none")} />
          分析なし
        </label>
        <label>
          <input type="radio" value="comment_analysis" checked={analysisType === "comment_analysis"} onChange={() => setAnalysisType("comment_analysis")} />
          コメント分析
        </label>
        <label>
          <input type="radio" value="channel_subscriber_popular_channel" checked={analysisType === "channel_subscriber_popular_channel"} onChange={() => setAnalysisType("channel_subscriber_popular_channel")} />
          視聴者人気のチャンネル分析
        </label>
      </div>

      <div className="flex-1 bg-gray-100 p-4 rounded overflow-y-auto">
        {messages.map((msg, idx) => renderMessage(msg, idx))}
      </div>

      {messages.length > 0 && messages[messages.length - 1].sender === "GPTまとめ" && (
        <button onClick={generatePDF} className="bg-red-500 text-white px-4 py-2 rounded mt-2">
          PDFで出力
        </button>
      )}

      <p className="mt-2">Status: {WebSocketManager.isConnected ? "Connected" : "Disconnected"}</p>
    </div>
  );
}
