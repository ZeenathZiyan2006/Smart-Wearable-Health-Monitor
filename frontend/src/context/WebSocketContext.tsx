import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useAuth } from './AuthContext';

interface WebSocketContextType {
  isConnected: boolean;
  lastMessage: any;
  sendMessage: (msg: string | object) => void;
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
}

const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  lastMessage: null,
  sendMessage: () => {},
  status: 'disconnected',
});

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<'connected' | 'connecting' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const pingIntervalRef = useRef<any>(null);

  const connect = () => {
    const token = localStorage.getItem('access_token');
    if (!token || !isAuthenticated) {
      setStatus('disconnected');
      setIsConnected(false);
      return;
    }

    try {
      setStatus('connecting');
      const wsUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1')
        .replace(/^http/, 'ws')
        + `/voice/ws?token=${encodeURIComponent(token)}`;

      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setStatus('connected');
        // Heartbeat ping every 25 seconds
        pingIntervalRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send('ping');
          }
        }, 25000);
      };

      socket.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const parsed = JSON.parse(event.data);
          setLastMessage(parsed);
        } catch {
          setLastMessage(event.data);
        }
      };

      socket.onerror = () => {
        setStatus('error');
      };

      socket.onclose = () => {
        setIsConnected(false);
        setStatus('disconnected');
        clearInterval(pingIntervalRef.current);
        // Automatic reconnection attempt with backoff
        if (isAuthenticated) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 5000);
        }
      };
    } catch {
      setStatus('error');
      setIsConnected(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    } else {
      if (wsRef.current) {
        wsRef.current.close();
      }
      setIsConnected(false);
      setStatus('disconnected');
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearTimeout(reconnectTimeoutRef.current);
      clearInterval(pingIntervalRef.current);
    };
  }, [isAuthenticated]);

  const sendMessage = (msg: string | object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = typeof msg === 'string' ? msg : JSON.stringify(msg);
      wsRef.current.send(payload);
    }
  };

  return (
    <WebSocketContext.Provider value={{ isConnected, lastMessage, sendMessage, status }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
