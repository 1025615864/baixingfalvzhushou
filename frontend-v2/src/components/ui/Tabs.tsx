/**
 * Tabs - 标签页组件
 */

import React, { useState } from 'react';

export interface TabsProps {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}

export interface TabsListProps {
  children: React.ReactNode;
  className?: string;
}

export interface TabsTriggerProps {
  value: string;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}

export interface TabsContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export function Tabs({ defaultValue, value, onValueChange, children, className = '' }: TabsProps) {
  const [internalValue, setInternalValue] = useState(defaultValue);
  const activeValue = value ?? internalValue;

  const handleValueChange = (newValue: string) => {
    if (value === undefined) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };

  return (
    <div className={className} data-value={activeValue}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<{ value?: string; onValueChange?: (value: string) => void }>, {
            value: activeValue,
            onValueChange: handleValueChange,
          });
        }
        return child;
      })}
    </div>
  );
}

export function TabsList({ children, className = '' }: TabsListProps) {
  return (
    <div className={`flex border-b border-gray-200 ${className}`}>
      {children}
    </div>
  );
}

export function TabsTrigger({ value, children, className = '', disabled = false }: TabsTriggerProps) {
  return (
    <button
      type="button"
      className={`px-4 py-2 text-sm font-medium border-b-2 border-transparent hover:border-gray-300 ${
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
      } ${className}`}
      data-state={value}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, children, className = '' }: TabsContentProps) {
  return (
    <div className={className} data-state={value}>
      {children}
    </div>
  );
}
