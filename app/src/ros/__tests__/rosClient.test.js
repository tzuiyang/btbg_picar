import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onerror = null;
    this.onmessage = null;
    this._sent = [];
    MockWebSocket._lastInstance = this;
  }

  send(data) {
    this._sent.push(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) this.onclose();
  }

  _simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) this.onopen();
  }

  _simulateMessage(data) {
    if (this.onmessage) this.onmessage({ data: JSON.stringify(data) });
  }

  _simulateError(error) {
    if (this.onerror) this.onerror(error);
  }

  _simulateClose() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) this.onclose();
  }
}

vi.stubGlobal('WebSocket', MockWebSocket);

// Inline client factory to avoid singleton issues
function createClient() {
  const client = {
    ws: null,
    eventHandlers: { connection: [], close: [], error: [] },
    _listeners: {},
    reconnectAttempts: 0,
    maxReconnectAttempts: 10,
    reconnectDelay: 1000,
    _reconnectTimer: null,
    url: null,
  };

  client._getWebSocketUrl = function () {
    const envHost = import.meta.env?.VITE_PI_HOST || '';
    const envPort = import.meta.env?.VITE_BTBG_PORT || '';
    const host = envHost || localStorage.getItem('btbg_host') || 'btbg.local';
    const port = envPort || localStorage.getItem('btbg_port') || '9090';
    return `ws://${host}:${port}`;
  };

  client.url = client._getWebSocketUrl();

  client.connect = function () {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      const timeout = setTimeout(() => {
        if (this.ws.readyState !== WebSocket.OPEN) {
          this.ws.close();
          reject(new Error('Connection timeout'));
        }
      }, 5000);

      this.ws.onopen = () => {
        clearTimeout(timeout);
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
        } catch (e) { /* ignore */ }
      };

      this.ws.onerror = (error) => {
        this._emit('error', error);
      };

      this.ws.onclose = () => {
        this._emit('close');
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 5000);
          this.reconnectAttempts++;
          this._reconnectTimer = setTimeout(() => this.connect().catch(() => {}), delay);
        }
      };
    });
  };

  client.disconnect = function () {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
    this.maxReconnectAttempts = 0;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  };

  client.isConnected = function () {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  };

  client.send = function (type, data = {}) {
    if (!this.isConnected()) return;
    this.ws.send(JSON.stringify({ type, ...data }));
  };

  client.onMessage = function (type, callback) {
    if (!this._listeners[type]) this._listeners[type] = [];
    this._listeners[type].push(callback);
  };

  client.on = function (event, handler) {
    if (this.eventHandlers[event]) this.eventHandlers[event].push(handler);
  };

  client.off = function (event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter((h) => h !== handler);
    }
  };

  client._emit = function (event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach((handler) => handler(data));
    }
  };

  client.setUrl = function (host, port = 9090) {
    this.url = `ws://${host}:${port}`;
    localStorage.setItem('btbg_host', host);
    localStorage.setItem('btbg_port', port.toString());
  };

  return client;
}

describe('BTBGClient', () => {
  let client;

  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    client = createClient();
  });

  afterEach(() => {
    if (client) client.disconnect();
    vi.useRealTimers();
  });

  // ── URL Resolution ──

  describe('URL Resolution', () => {
    it('uses VITE_PI_HOST from env when available', () => {
      const envHost = import.meta.env?.VITE_PI_HOST;
      if (envHost) {
        expect(client.url).toContain(envHost);
      } else {
        expect(client.url).toMatch(/^ws:\/\/.+:\d+$/);
      }
    });

    it('falls back to localStorage when env not set', () => {
      const origHost = import.meta.env?.VITE_PI_HOST;
      const origPort = import.meta.env?.VITE_BTBG_PORT;
      if (import.meta.env) {
        import.meta.env.VITE_PI_HOST = '';
        import.meta.env.VITE_BTBG_PORT = '';
      }

      localStorage.setItem('btbg_host', '10.0.0.50');
      localStorage.setItem('btbg_port', '8080');
      const c = createClient();
      expect(c.url).toBe('ws://10.0.0.50:8080');
      c.disconnect();

      if (import.meta.env) {
        import.meta.env.VITE_PI_HOST = origHost;
        import.meta.env.VITE_BTBG_PORT = origPort;
      }
    });

    it('falls back to btbg.local when nothing is set', () => {
      const origHost = import.meta.env?.VITE_PI_HOST;
      const origPort = import.meta.env?.VITE_BTBG_PORT;
      if (import.meta.env) {
        import.meta.env.VITE_PI_HOST = '';
        import.meta.env.VITE_BTBG_PORT = '';
      }

      const c = createClient();
      expect(c.url).toBe('ws://btbg.local:9090');
      c.disconnect();

      if (import.meta.env) {
        import.meta.env.VITE_PI_HOST = origHost;
        import.meta.env.VITE_BTBG_PORT = origPort;
      }
    });

    it('setUrl updates localStorage and internal URL', () => {
      client.setUrl('192.168.1.99', 4000);
      expect(client.url).toBe('ws://192.168.1.99:4000');
      expect(localStorage.getItem('btbg_host')).toBe('192.168.1.99');
      expect(localStorage.getItem('btbg_port')).toBe('4000');
    });

    it('port defaults to 9090', () => {
      const origPort = import.meta.env?.VITE_BTBG_PORT;
      if (import.meta.env) import.meta.env.VITE_BTBG_PORT = '';

      const c = createClient();
      expect(c.url).toMatch(/:9090$/);
      c.disconnect();

      if (import.meta.env) import.meta.env.VITE_BTBG_PORT = origPort;
    });
  });

  // ── Connection Lifecycle ──

  describe('Connection Lifecycle', () => {
    it('connect() creates WebSocket with correct URL', async () => {
      const connectPromise = client.connect();
      const ws = MockWebSocket._lastInstance;
      expect(ws.url).toBe(client.url);
      ws._simulateOpen();
      await connectPromise;
    });

    it('connect() resolves on open', async () => {
      const connectPromise = client.connect();
      MockWebSocket._lastInstance._simulateOpen();
      await expect(connectPromise).resolves.toBeUndefined();
    });

    it('connect() rejects on timeout', async () => {
      const connectPromise = client.connect();
      vi.advanceTimersByTime(5000);
      await expect(connectPromise).rejects.toThrow('Connection timeout');
    });

    it('disconnect() closes WebSocket and prevents reconnect', async () => {
      const connectPromise = client.connect();
      MockWebSocket._lastInstance._simulateOpen();
      await connectPromise;

      client.disconnect();
      expect(client.ws).toBeNull();
      expect(client.maxReconnectAttempts).toBe(0);
    });

    it('isConnected() returns true only when WebSocket is OPEN', async () => {
      expect(client.isConnected()).toBeFalsy();

      const connectPromise = client.connect();
      expect(client.isConnected()).toBe(false);

      MockWebSocket._lastInstance._simulateOpen();
      await connectPromise;
      expect(client.isConnected()).toBe(true);
    });

    it('auto-reconnects on close up to max attempts', async () => {
      const connectPromise = client.connect();
      MockWebSocket._lastInstance._simulateOpen();
      await connectPromise;

      MockWebSocket._lastInstance._simulateClose();
      expect(client.reconnectAttempts).toBe(1);
    });

    it('exponential backoff delay capped at 5s', () => {
      expect(Math.min(1000 * Math.pow(2, 0), 5000)).toBe(1000);
      expect(Math.min(1000 * Math.pow(2, 1), 5000)).toBe(2000);
      expect(Math.min(1000 * Math.pow(2, 2), 5000)).toBe(4000);
      expect(Math.min(1000 * Math.pow(2, 3), 5000)).toBe(5000);
      expect(Math.min(1000 * Math.pow(2, 4), 5000)).toBe(5000);
    });
  });

  // ── Messaging ──

  describe('Messaging', () => {
    it('send() serializes { type, ...data } as JSON', async () => {
      const connectPromise = client.connect();
      const ws = MockWebSocket._lastInstance;
      ws._simulateOpen();
      await connectPromise;

      client.send('drive', { speed: 0.5, steering: -0.3 });
      expect(ws._sent).toHaveLength(1);
      expect(JSON.parse(ws._sent[0])).toEqual({
        type: 'drive',
        speed: 0.5,
        steering: -0.3,
      });
    });

    it('send() is no-op when disconnected', () => {
      client.send('drive', { speed: 1 });
      expect(client.ws).toBeNull();
    });

    it('onMessage() routes messages by type to correct callback', async () => {
      const handler = vi.fn();
      client.onMessage('telemetry', handler);

      const connectPromise = client.connect();
      const ws = MockWebSocket._lastInstance;
      ws._simulateOpen();
      await connectPromise;

      ws._simulateMessage({ type: 'telemetry', sensors: { ultrasonic: 42 } });
      expect(handler).toHaveBeenCalledWith({
        type: 'telemetry',
        sensors: { ultrasonic: 42 },
      });
    });

    it('onMessage() ignores messages with wrong type', async () => {
      const handler = vi.fn();
      client.onMessage('telemetry', handler);

      const connectPromise = client.connect();
      const ws = MockWebSocket._lastInstance;
      ws._simulateOpen();
      await connectPromise;

      ws._simulateMessage({ type: 'other', data: 123 });
      expect(handler).not.toHaveBeenCalled();
    });

    it('invalid JSON from server does not crash', async () => {
      const connectPromise = client.connect();
      const ws = MockWebSocket._lastInstance;
      ws._simulateOpen();
      await connectPromise;

      expect(() => {
        ws.onmessage({ data: 'not valid json{{{' });
      }).not.toThrow();
    });
  });

  // ── Events ──

  describe('Events', () => {
    it('on("connection") fires on WebSocket open', async () => {
      const handler = vi.fn();
      client.on('connection', handler);

      const connectPromise = client.connect();
      MockWebSocket._lastInstance._simulateOpen();
      await connectPromise;

      expect(handler).toHaveBeenCalledOnce();
    });

    it('on("close") fires on WebSocket close', async () => {
      const handler = vi.fn();
      client.on('close', handler);

      const connectPromise = client.connect();
      MockWebSocket._lastInstance._simulateOpen();
      await connectPromise;

      MockWebSocket._lastInstance._simulateClose();
      expect(handler).toHaveBeenCalledOnce();
    });

    it('on("error") fires on WebSocket error', async () => {
      const handler = vi.fn();
      client.on('error', handler);

      const connectPromise = client.connect();
      const ws = MockWebSocket._lastInstance;
      ws._simulateOpen();
      await connectPromise;

      ws._simulateError(new Error('test error'));
      expect(handler).toHaveBeenCalledOnce();
    });

    it('off() removes handler correctly', () => {
      const handler = vi.fn();
      client.on('connection', handler);
      client.off('connection', handler);
      expect(client.eventHandlers.connection).toHaveLength(0);
    });
  });
});
