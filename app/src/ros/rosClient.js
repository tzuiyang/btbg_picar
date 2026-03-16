/**
 * WebSocket Client - Plain WebSocket replacement for roslibjs.
 *
 * Sends/receives JSON messages directly to the BTBG Python server.
 * Drop-in API replacement: connect, disconnect, publish, subscribe, on/off.
 */

class BTBGClient {
  constructor() {
    this.ws = null;
    this.eventHandlers = {
      connection: [],
      close: [],
      error: [],
    };

    // Message listeners keyed by message type
    this._listeners = {};

    // Connection settings
    this.url = this._getWebSocketUrl();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this._reconnectTimer = null;
  }

  _getWebSocketUrl() {
    const envHost = typeof import.meta !== 'undefined' && import.meta.env?.VITE_PI_HOST;
    const envPort = typeof import.meta !== 'undefined' && import.meta.env?.VITE_BTBG_PORT;
    const host = envHost || localStorage.getItem('btbg_host') || 'btbg.local';
    const port = envPort || localStorage.getItem('btbg_port') || '9090';
    console.log(`WebSocket target: ${host}:${port} (source: ${envHost ? '.env' : localStorage.getItem('btbg_host') ? 'localStorage' : 'fallback'})`);
    return `ws://${host}:${port}`;
  }

  connect() {
    return new Promise((resolve, reject) => {
      console.log(`Connecting to ${this.url}...`);

      this.ws = new WebSocket(this.url);

      const timeout = setTimeout(() => {
        if (this.ws.readyState !== WebSocket.OPEN) {
          this.ws.close();
          reject(new Error('Connection timeout'));
        }
      }, 5000);

      this.ws.onopen = () => {
        clearTimeout(timeout);
        console.log('Connected to BTBG server');
        this.reconnectAttempts = 0;
        this._emit('connection');
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const type = msg.type;
          if (type && this._listeners[type]) {
            this._listeners[type].forEach((cb) => cb(msg));
          }
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this._emit('error', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this._emit('close');

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            5000
          );
          this.reconnectAttempts++;
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
          this._reconnectTimer = setTimeout(() => this.connect().catch(() => {}), delay);
        }
      };
    });
  }

  disconnect() {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
    this.maxReconnectAttempts = 0; // prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Send a JSON message to the server.
   * @param {string} type - Message type (e.g. "drive", "mode", "servo", "stop")
   * @param {object} data - Payload (merged with {type})
   */
  send(type, data = {}) {
    if (!this.isConnected()) {
      return;
    }
    this.ws.send(JSON.stringify({ type, ...data }));
  }

  /**
   * Listen for messages of a given type from the server.
   * @param {string} type - Message type to listen for (e.g. "telemetry")
   * @param {function} callback - Handler function
   */
  onMessage(type, callback) {
    if (!this._listeners[type]) {
      this._listeners[type] = [];
    }
    this._listeners[type].push(callback);
  }

  /**
   * Register event handler (connection, close, error).
   */
  on(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].push(handler);
    }
  }

  off(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter((h) => h !== handler);
    }
  }

  _emit(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach((handler) => handler(data));
    }
  }

  setUrl(host, port = 9090) {
    this.url = `ws://${host}:${port}`;
    localStorage.setItem('btbg_host', host);
    localStorage.setItem('btbg_port', port.toString());
  }
}

// Export singleton
export const btbgClient = new BTBGClient();
// Keep named export compatible with old imports
export const rosClient = btbgClient;
export default btbgClient;
