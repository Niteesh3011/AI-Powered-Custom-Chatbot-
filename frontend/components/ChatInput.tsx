"use client";
import { Send } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative flex items-end w-full max-w-3xl mx-auto bg-muted/20 border border-muted-foreground/20 rounded-3xl overflow-hidden focus-within:ring-1 focus-within:ring-primary/50 focus-within:border-primary/50 transition-all shadow-sm">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Message Medbot..."
        className="w-full bg-transparent pl-5 pr-14 py-3.5 text-sm sm:text-base focus:outline-none resize-none min-h-[52px] max-h-[200px]"
        rows={1}
        disabled={disabled}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="absolute right-2 bottom-2 p-2 rounded-full bg-primary text-primary-foreground disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors flex items-center justify-center h-[36px] w-[36px]"
      >
        <Send size={16} className="ml-0.5" />
      </button>
    </div>
  );
}
