import { useState, useRef, useEffect } from 'react';

export interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
  defaultExpanded?: string[];
  className?: string;
}

export function Accordion({
  items,
  allowMultiple = false,
  defaultExpanded = [],
  className = '',
}: AccordionProps) {
  const [expanded, setExpanded] = useState<string[]>(defaultExpanded);

  const handleToggle = (id: string) => {
    if (allowMultiple) {
      setExpanded(prev =>
        prev.includes(id)
          ? prev.filter(item => item !== id)
          : [...prev, id]
      );
    } else {
      setExpanded(prev =>
        prev.includes(id) ? [] : [id]
      );
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {items.map(item => (
        <div key={item.id} className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => !item.disabled && handleToggle(item.id)}
            disabled={item.disabled}
            className={`w-full flex items-center justify-between px-4 py-3 text-left font-medium transition-colors ${
              item.disabled
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white hover:bg-gray-50 text-gray-900'
            }`}
          >
            {item.title}
            <svg
              className={`w-5 h-5 transition-transform ${
                expanded.includes(item.id) ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expanded.includes(item.id) && !item.disabled && (
            <div className="px-4 py-3 bg-gray-50 text-gray-700 border-t border-gray-200">
              {item.content}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
