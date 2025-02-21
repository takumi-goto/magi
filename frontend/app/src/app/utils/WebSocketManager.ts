class WebSocketManager {
  private static instance: WebSocketManager;
  private socket: WebSocket | null = null;
  private listeners: ((message: MessageEvent) => void)[] = [];
  private connectionStatus: boolean = false;

  private constructor() {}

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  connect(url: string) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return; // ✅ 既に接続済みなら新しい接続を作らない
    }

    console.log("WebSocket: 接続開始");
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("WebSocket: 接続成功");
      this.connectionStatus = true;
    };

    this.socket.onmessage = (event) => {
      this.listeners.forEach((listener) => listener(event));
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket: エラー発生", error);
    };

    this.socket.onclose = (event) => {
      console.log("WebSocket: 切断", event);
      this.connectionStatus = false;
      this.socket = null;
      setTimeout(() => this.connect(url), 3000); // 3秒後に再接続
    };
  }

  addListener(listener: (message: MessageEvent) => void) {
    this.listeners.push(listener);
  }

  removeListener(listener: (message: MessageEvent) => void) {
    this.listeners = this.listeners.filter((l) => l !== listener);
  }

  close() {
    if (this.socket) {
      this.socket.close();
    }
  }

  /** ✅ 外部から WebSocket の接続状態を取得する */
  get isConnected() {
    return this.connectionStatus;
  }

  /** ✅ 外部から WebSocket インスタンスにアクセスする */
  get socketInstance(): WebSocket | null {
    return this.socket;
  }
}

export default WebSocketManager.getInstance();
