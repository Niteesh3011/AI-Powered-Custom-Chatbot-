import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export type MessageRole = 'user' | 'bot';

export interface ChatMessageProps {
  role: MessageRole;
  content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === 'user';
  
  return (
    <div className={`py-6 px-4 sm:px-6 flex gap-4 sm:gap-6 ${isUser ? '' : 'bg-muted/30'}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${isUser ? 'bg-muted-foreground text-background' : 'bg-primary text-primary-foreground'}`}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>
      <div className="flex-1 text-sm sm:text-base leading-relaxed break-words space-y-4">
        <ReactMarkdown
          components={{
            p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
            ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2" {...props} />,
            ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2" {...props} />,
            li: ({node, ...props}) => <li className="mb-1" {...props} />,
            h1: ({node, ...props}) => <h1 className="text-2xl font-bold mb-2" {...props} />,
            h2: ({node, ...props}) => <h2 className="text-xl font-bold mb-2" {...props} />,
            h3: ({node, ...props}) => <h3 className="text-lg font-bold mb-2" {...props} />,
            code: ({node, inline, ...props}: any) => 
              inline ? 
                <code className="bg-black/30 px-1 py-0.5 rounded text-sm font-mono" {...props} /> : 
                <pre className="bg-black/50 p-4 rounded-lg overflow-x-auto text-sm font-mono my-2"><code {...props} /></pre>
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
