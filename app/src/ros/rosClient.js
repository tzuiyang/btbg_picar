/**
 * ROS Client - Singleton wrapper around roslibjs
 *
 * Provides:
 * - Automatic connection management
 * - Topic subscription/publishing helpers
 * - Event emitter for connection state
 */

import ROSLIB from 'roslib';

class ROSClient {
  constructor() {
    this.ros = null;
    this.topics = {};
    this.subscribers = {};
    this.eventHandlers = {
      connection: [],
      close: [],
      error: [],
    };

    // Connection settings
    this.url = this._getWebSocketUrl();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
  }

  /**
   * Get WebSocket URL from environment or default
   */
  _getWebSocketUrl() {
    // Check for environment variable (can be set in .env)
    if (typeof process !== 'undefined' && process.env.ROSBRIDGE_URL) {
      return process.env.ROSBRIDGE_URL;
    }

    // Default to btbg.local
    const host = localStorage.getItem('rosbridge_host') || 'btbg.local';
    const port = localStorage.getItem('rosbridge_port') || '9090';
    return `ws://${host}:${port}`;
  }

  /**
   * Connect to rosbridge
   */
  connect() {
    return new Promise((resolve, reject) => {
      console.log(`Connecting to ${this.url}...`);

      this.ros = new ROSLIB.Ros({
        url: this.url,
      });

      this.ros.on('connection', () => {
        console.log('Connected to rosbridge');
        this.reconnectAttempts = 0;
        this._emit('connection');
        resolve();
      });

      this.ros.on('error', (error) => {
        console.error('rosbridge error:', error);
        this._emit('error', error);
      });

      this.ros.on('close', () => {
        console.log('rosbridge connection closed');
        this._emit('close');

        // Auto-reconnect with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            5000
          );
          this.reconnectAttempts++;
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        }
      });

      // Timeout after 5 seconds
      setTimeout(() => {
        if (!this.ros.isConnected) {
          reject(new Error('Connection timeout'));
        }
      }, 5000);
    });
  }

  /**
   * Disconnect from rosbridge
   */
  disconnect() {
    if (this.ros) {
      // Unsubscribe from all topics
      Object.values(this.subscribers).forEach(sub => sub.unsubscribe());
      this.subscribers = {};

      this.ros.close();
      this.ros = null;
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.ros && this.ros.isConnected;
  }

  /**
   * Get or create a topic
   */
  getTopic(name, messageType) {
    const key = `${name}:${messageType}`;
    if (!this.topics[key]) {
      this.topics[key] = new ROSLIB.Topic({
        ros: this.ros,
        name: name,
        messageType: messageType,
      });
    }
    return this.topics[key];
  }

  /**
   * Subscribe to a topic
   */
  subscribe(topicConfig, callback) {
    const { name, messageType } = topicConfig;
    const topic = this.getTopic(name, messageType);

    const subscriber = topic.subscribe(callback);
    this.subscribers[name] = topic;

    console.log(`Subscribed to ${name}`);
    return () => {
      topic.unsubscribe();
      delete this.subscribers[name];
    };
  }

  /**
   * Publish to a topic
   */
  publish(topicConfig, data) {
    if (!this.isConnected()) {
      console.warn('Cannot publish: not connected');
      return;
    }

    const { name, messageType } = topicConfig;
    const topic = this.getTopic(name, messageType);
    const message = new ROSLIB.Message(data);

    topic.publish(message);
  }

  /**
   * Register event handler
   */
  on(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].push(handler);
    }
  }

  /**
   * Remove event handler
   */
  off(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
    }
  }

  /**
   * Emit event
   */
  _emit(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data));
    }
  }

  /**
   * Set connection URL
   */
  setUrl(host, port = 9090) {
    this.url = `ws://${host}:${port}`;
    localStorage.setItem('rosbridge_host', host);
    localStorage.setItem('rosbridge_port', port.toString());
  }
}

// Export singleton instance
export const rosClient = new ROSClient();
export default rosClient;
