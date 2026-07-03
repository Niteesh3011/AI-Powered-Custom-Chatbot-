"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage, MessageRole } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { Activity, Stethoscope, ShieldPlus, HeartPulse } from "lucide-react";

interface Message {
  role: MessageRole;
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
      const response = await fetch('http://localhost:8080/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: content }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
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
          content: "I'm sorry, I'm having trouble connecting to my servers right now. Please make sure the backend server (`python app.py`) is running on port 8080."
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
    <div className="flex flex-col h-screen bg-background text-foreground selection:bg-primary/30">
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b border-muted/20 backdrop-blur-md bg-background/80 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Activity size={20} />
          </div>
          <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">Medbot</h1>
        </div>
        {messages.length > 0 && (
           <button 
            onClick={() => setMessages([])}
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-full hover:bg-muted/50"
          >
            New Chat
          </button>
        )}
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto flex flex-col pb-4 h-full">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-12 transition-opacity duration-700">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-2xl shadow-blue-500/20 mb-8 transform hover:scale-105 transition-transform">
                <Activity size={40} />
              </div>
              <h2 className="text-3xl sm:text-5xl font-bold mb-4 tracking-tight text-center bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
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
                    className="flex flex-col items-start p-5 rounded-2xl bg-muted/20 border border-muted/30 hover:bg-muted/40 hover:border-primary/50 transition-all text-left group"
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
                      <div className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '300ms' }} />
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
  );
}
