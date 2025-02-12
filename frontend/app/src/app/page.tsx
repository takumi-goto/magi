"use client";

import { useEffect, useState, useRef } from "react";

interface Message {
  sender: string;  // 例: "User" | "GPT(3.5)" | "Gemini(2.0)" | "GPTまとめ"
  text: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [topic, setTopic] = useState("");
  const [analysisType, setAnalysisType] = useState("none"); // "video_analysis" | "channel_subscriber_popular_channel"
  const [videoId, setVideoId] = useState(""); // コメント分析のときのみ必要
  const [channelId, setChannelId] = useState(""); // 視聴者人気のチャンネル分析のときのみ必要
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket("ws://localhost:8001/ws");
      socketRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket 接続成功");
        setIsConnected(true);
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as Message;
          setMessages((prev) => [...prev, data]);
        } catch (error) {
          console.error("メッセージのパースエラー:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket エラー:", error);
      };

      ws.onclose = () => {
        console.log("WebSocket切断");
        setIsConnected(false);
      };
    };

    connectWebSocket();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const sendMessage = () => {
    if (socketRef.current && isConnected) {
      const payload = {
        topic: topic,
        analysisType: analysisType !== "none" ? analysisType : undefined,
        videoId: analysisType === "video_analysis" ? videoId : undefined, // コメント分析時のみ送信
        channelId: analysisType === "channel_subscriber_popular_channel" ? channelId : undefined, // 視聴者人気のチャンネル分析時のみ送信
      };

      console.log("送信データ:", payload);
      setMessages((prev) => [...prev, { sender: "User", text: topic }]);
      socketRef.current.send(JSON.stringify(payload));
      setTopic("");
    } else {
      console.warn("WebSocket未接続です");
    }
  };

  // メッセージ描画
  const renderMessage = (msg: Message, index: number) => {
    const sender = msg.sender;

    let alignment = "justify-start";
    let bgColor = "bg-blue-200";

    if (sender.includes("Gemini")) {
      alignment = "justify-end";
      bgColor = "bg-green-200";
    } else if (sender === "User") {
      alignment = "justify-center";
      bgColor = "bg-gray-300";
    }

    return (
      <div key={index} className={`flex mb-2 ${alignment}`}>
        <div className={`p-2 rounded-lg max-w-xs ${bgColor}`}>
          <strong>{sender}:</strong> {msg.text}
        </div>
      </div>
    );
  };

  return (
    <div className="h-screen flex flex-col p-4">
      {/* ヘッダー */}
      <h1 className="text-2xl font-bold mb-4">MAG(K)I波MARI イラストりあす</h1>

      {/* メッセージ入力 */}
      <div className="mt-4 flex space-x-2">
        <input
          className="border p-2 flex-1"
          type="text"
          placeholder="議題やメッセージを入力..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />
        <button
          onClick={sendMessage}
          className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
          disabled={!isConnected || !topic.trim()}
        >
          送信
        </button>
      </div>

      {/* ラジオボタン: 分析タイプ選択 */}
      <div className="mb-4">
        <p className="font-bold">分析タイプを選択:</p>
        <label className="mr-4">
          <input
            type="radio"
            value="none"
            checked={analysisType === "none"}
            onChange={() => setAnalysisType("none")}
          />
          分析なし
        </label>
        <label className="mr-4">
          <input
            type="radio"
            value="video_analysis"
            checked={analysisType === "video_analysis"}
            onChange={() => setAnalysisType("video_analysis")}
          />
          コメント分析
        </label>
        <label>
          <input
            type="radio"
            value="channel_subscriber_popular_channel"
            checked={analysisType === "channel_subscriber_popular_channel"}
            onChange={() => setAnalysisType("channel_subscriber_popular_channel")}
          />
          視聴者人気のチャンネル分析
        </label>
      </div>

      {/* コメント分析を選択したら動画ID入力を表示 */}
      {analysisType === "video_analysis" && (
        <div className="mb-4">
          <p className="font-bold">動画IDを入力:</p>
          <input
            className="border p-2 w-full"
            type="text"
            placeholder="動画IDを入力..."
            value={videoId}
            onChange={(e) => setVideoId(e.target.value)}
          />
        </div>
      )}

      {/* 視聴者に人気のチャンネルを選択したら動画ID入力を表示 */}
      {analysisType === "channel_subscriber_popular_channel" && (
        <div className="mb-4">
          <p className="font-bold">チャンネルIDを入力:</p>
          <input
            className="border p-2 w-full"
            type="text"
            placeholder="UC..."
            value={videoId}
            onChange={(e) => setChannelId(e.target.value)}
          />
        </div>
      )}

      {/* メッセージ表示エリア */}
      <div className="flex-1 bg-gray-100 p-4 rounded overflow-y-auto">
        {messages.map((msg, idx) => renderMessage(msg, idx))}
      </div>

      {/* 接続ステータス */}
      <p className="mt-2">Status: {isConnected ? "Connected" : "Disconnected"}</p>
    </div>
  );
}
