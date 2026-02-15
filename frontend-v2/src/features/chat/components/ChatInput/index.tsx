import { useState, type FormEvent, type KeyboardEvent } from 'react';

import { Button } from '@/shared/components/Button';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  isLoading,
  placeholder = '输入您的问题...',
}: ChatInputProps): JSX.Element {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4 bg-white">
      <div className="flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent max-h-32"
          disabled={isLoading}
        />
        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
          disabled={!input.trim() || isLoading}
          className="px-6"
        >
          发送
        </Button>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        按 Enter 发送，Shift + Enter 换行
      </p>
    </form>
  );
}