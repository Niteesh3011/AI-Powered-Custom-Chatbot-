"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChatMessage, MessageRole } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { Activity, Stethoscope, ShieldPlus, HeartPulse, LogOut, Plus, MessageSquare, Menu, X } from "lucide-react";

interface Message {
  role: MessageRole;
  content: string;
}

interface Session {
  id: string;
  title: string;
  updated_at: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState<{full_name: string, email: string} | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Authentication check and fetch sessions
  useEffect(() => {
    const token = localStorage.getItem("medbot_token");
    const userStr = localStorage.getItem("medbot_user");
    if (!token) {
      router.push("/login");
    } else {
      if (userStr) {
        try {
          setUser(JSON.parse(userStr));
        } catch (e) {
          console.error("Failed to parse user data", e);
        }
      }
      fetchSessions(token);
    }
  }, [router]);

  const fetchSessions = async (token: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      const response = await fetch(`${apiUrl}/api/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions);
      }
    } catch (e) {
      console.error("Failed to fetch sessions", e);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const token = localStorage.getItem("medbot_token");
      if (!token) return;
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      const response = await fetch(`${apiUrl}/api/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages.map((m: any) => ({
          role: m.role,
          content: m.content
        })));
        setCurrentSessionId(sessionId);
        if (window.innerWidth < 768) {
          setSidebarOpen(false);
        }
      }
    } catch (e) {
      console.error("Failed to load session", e);
    }
  };

  const startNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("medbot_token");
    localStorage.removeItem("medbot_user");
    router.push("/login");
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (content: string) => {
    // Add user message
    const newMessages = [...messages, { role: 'user' as MessageRole, content }];
    setMessages(newMessages);
    setIsTyping(true);

    try {
      const token = localStorage.getItem("medbot_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          query: content,
          session_id: currentSessionId,
          chat_history: messages.map(msg => ({ role: msg.role, content: msg.content }))
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.session_id && data.session_id !== currentSessionId) {
        setCurrentSessionId(data.session_id);
        fetchSessions(token); // refresh sidebar
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          content: data.response
        }
      ]);
    } catch (error) {
      console.error("Error fetching from backend:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          content: "I'm sorry, I'm having trouble connecting to my servers right now. Please make sure the backend server (`python app.py`) is running."
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const suggestions = [
    {
      icon: <Stethoscope className="w-5 h-5 text-blue-400" />,
      title: "Check symptoms",
      text: "I have a headache and mild fever. What could it be?"
    },
    {
      icon: <ShieldPlus className="w-5 h-5 text-green-400" />,
      title: "Preventive care",
      text: "What are the best practices for preventing the flu?"
    },
    {
      icon: <HeartPulse className="w-5 h-5 text-red-400" />,
      title: "Heart health",
      text: "How can I improve my cardiovascular health?"
    },
    {
      icon: <Activity className="w-5 h-5 text-purple-400" />,
      title: "General wellness",
      text: "What is a balanced diet for an adult?"
    }
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden selection:bg-primary/30">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-72 bg-slate-950 text-slate-200 transform ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out flex flex-col border-r border-slate-800 shadow-2xl md:shadow-none`}>
        <div className="p-3 pb-0">
          <button 
            onClick={startNewChat}
            className="flex w-full items-center gap-3 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 p-3 text-sm transition-colors text-white font-medium shadow-sm"
          >
            <Plus size={18} />
            <span>New Chat</span>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="text-xs font-bold text-slate-500 mb-3 px-2 mt-4 uppercase tracking-wider">Chat History</div>
          {sessions.length === 0 ? (
            <div className="text-sm text-slate-500 px-2 italic">No previous chats</div>
          ) : (
            sessions.map(session => (
              <button
                key={session.id}
                onClick={() => loadSession(session.id)}
                className={`flex w-full items-center gap-3 rounded-lg p-3 text-sm transition-colors text-left truncate ${currentSessionId === session.id ? 'bg-slate-800 text-white shadow-sm font-medium' : 'hover:bg-slate-800/50 text-slate-400 hover:text-slate-200'}`}
              >
                <MessageSquare size={16} className="shrink-0" />
                <span className="truncate">{session.title}</span>
              </button>
            ))
          )}
        </div>
        
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex flex-col gap-3">
          {user && (
            <div className="flex items-center gap-3 w-full">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md font-bold shrink-0">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-medium text-slate-200 truncate">{user.full_name || 'User'}</span>
                <span className="text-xs text-slate-400 truncate">{user.email}</span>
              </div>
            </div>
          )}
          <button 
            onClick={handleLogout}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-700/50 hover:bg-slate-800 p-2 text-sm transition-colors text-slate-300 hover:text-red-400 font-medium md:hidden"
          >
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen bg-background">
        {/* Header */}
        <header className="flex items-center justify-between p-4 border-b border-muted/20 backdrop-blur-md bg-background/80 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <button 
              className="md:hidden p-2 -ml-2 text-muted-foreground hover:text-foreground rounded-md hover:bg-muted/50"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={20} />
            </button>
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 hidden sm:flex">
              <Activity size={20} />
            </div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-500 to-indigo-500 bg-clip-text text-transparent">Medbot</h1>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-red-400 transition-colors px-3 py-1.5 rounded-full hover:bg-red-400/10 ml-2"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>

        {/* Chat Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto flex flex-col pb-4 h-full">
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-12 transition-opacity duration-700">
                <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-2xl shadow-blue-500/20 mb-8 transform hover:scale-105 transition-transform">
                  <Activity size={40} />
                </div>
                <h2 className="text-3xl sm:text-5xl font-bold mb-4 tracking-tight text-center bg-gradient-to-r from-blue-500 to-indigo-400 bg-clip-text text-transparent">
                  How can I help you today?
                </h2>
                <p className="text-muted-foreground text-center max-w-xl text-lg mb-12">
                  I'm your personal AI medical assistant. Ask me anything about symptoms, conditions, or general health.
                </p>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSend(suggestion.text)}
                      className="flex flex-col items-start p-5 rounded-2xl bg-muted/20 border border-muted/30 hover:bg-muted/40 hover:border-blue-500/50 transition-all text-left group"
                    >
                      <div className="mb-3 p-2 rounded-xl bg-background/50 group-hover:bg-background transition-colors shadow-sm">
                        {suggestion.icon}
                      </div>
                      <h3 className="font-semibold text-foreground mb-1">{suggestion.title}</h3>
                      <p className="text-sm text-muted-foreground line-clamp-2">{suggestion.text}</p>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                {messages.map((msg, index) => (
                  <ChatMessage key={index} role={msg.role} content={msg.content} />
                ))}
                {isTyping && (
                  <div className="py-8 px-4 sm:px-6 flex gap-4 sm:gap-6 bg-muted/10">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
                      <Activity size={18} className="animate-pulse" />
                    </div>
                    <div className="flex-1 flex items-center">
                      <div className="flex space-x-1.5">
                        <div className="w-2 h-2 rounded-full bg-blue-500/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 rounded-full bg-blue-500/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 rounded-full bg-blue-500/50 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} className="h-4" />
              </div>
            )}
          </div>
        </main>

        {/* Input Area */}
        <div className="p-4 pt-6 bg-gradient-to-t from-background via-background to-transparent sticky bottom-0">
          <ChatInput onSend={handleSend} disabled={isTyping} />
          <p className="text-center text-xs text-muted-foreground mt-4 pb-2 font-medium">
            Medbot can make mistakes. Consider verifying important health information.
          </p>
        </div>
      </div>
    </div>
  );
}
