/**
 * 表单数据自动保存 Hook
 * 提供表单数据的自动保存、恢复和清理功能
 */

import { useState, useEffect, useCallback, useRef } from 'react';

import { Persistence, EXPIRE_TIMES } from './persistence';

// ==================== 类型定义 ====================

/** 表单持久化选项 */
export interface FormPersistenceOptions<T> {
  /** 表单唯一标识 */
  formKey: string;
  /** 初始值 */
  initialValue: T;
  /** 自动保存间隔（毫秒），默认 1000ms，0 表示禁用 */
  autoSaveInterval?: number;
  /** 过期时间（毫秒），默认 24 小时 */
  expireTime?: number;
  /** 存储类型 */
  storage?: 'local' | 'session';
  /** 是否在组件卸载时清除数据 */
  clearOnUnmount?: boolean;
  /** 是否在提交成功后清除数据 */
  clearOnSubmit?: boolean;
  /** 数据变更回调 */
  onChange?: (data: T) => void;
  /** 数据恢复回调 */
  onRestore?: (data: T) => void;
  /** 是否启用调试日志 */
  debug?: boolean;
}

/** 表单持久化返回值 */
export interface FormPersistenceReturn<T> {
  /** 当前表单数据 */
  data: T;
  /** 设置表单数据 */
  setData: (data: T | ((prev: T) => T)) => void;
  /** 重置为初始值 */
  reset: () => void;
  /** 手动保存 */
  save: () => void;
  /** 清除保存的数据 */
  clear: () => void;
  /** 是否有保存的数据 */
  hasSavedData: boolean;
  /** 是否已修改 */
  isDirty: boolean;
  /** 最后保存时间 */
  lastSavedAt: Date | null;
  /** 恢复保存的数据 */
  restore: () => void;
}

/** 保存的表单数据结构 */
interface SavedFormData<T> {
  /** 表单数据 */
  data: T;
  /** 保存时间 */
  savedAt: number;
}

// ==================== 工具函数 ====================

/**
 * 生成表单存储键
 */
function getFormStorageKey(formKey: string): string {
  return `form_${formKey}`;
}

/**
 * 深度比较两个对象是否相等
 */
function deepEqual<T>(a: T, b: T): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

/**
 * 深度克隆对象
 */
function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  return structuredClone(obj);
}

// ==================== useFormField Hook ====================

/**
 * 单个表单字段持久化 Hook
 */
export function useFormField<T>(
  formKey: string,
  fieldName: string,
  initialValue: T,
  options?: Partial<FormPersistenceOptions<Record<string, T>>>
): [T, (value: T) => void, () => void] {
  const { data, setData, clear } = useFormPersistence<Record<string, T>>(
    formKey,
    { [fieldName]: initialValue },
    options
  );

  const fieldValue = data[fieldName] ?? initialValue;

  const setFieldValue = useCallback(
    (value: T) => {
      setData((prev) => ({
        ...prev,
        [fieldName]: value,
      }));
    },
    [setData, fieldName]
  );

  const clearField = useCallback(() => {
    clear();
  }, [clear]);

  return [fieldValue, setFieldValue, clearField];
}

// ==================== useFormPersistence Hook ====================

/**
 * 表单数据持久化 Hook
 * 自动保存表单数据到本地存储，并在组件重新加载时恢复
 * 
 * @example
 * ```tsx
 * interface MyFormData {
 *   name: string;
 *   email: string;
 *   message: string;
 * }
 * 
 * function MyForm() {
 *   const { data, setData, save, clear, isDirty } = useFormPersistence<MyFormData>(
 *     'my-form',
 *     { name: '', email: '', message: '' }
 *   );
 * 
 *   return (
 *     <form>
 *       <input
 *         value={data.name}
 *         onChange={(e) => setData({ ...data, name: e.target.value })}
 *       />
 *       <button type="button" onClick={save}>保存草稿</button>
 *       <button type="button" onClick={clear}>清除</button>
 *     </form>
 *   );
 * }
 * ```
 */
export function useFormPersistence<T extends Record<string, unknown>>(
  formKey: string,
  initialValue: T,
  options: Partial<FormPersistenceOptions<T>> = {}
): FormPersistenceReturn<T> {
  const {
    autoSaveInterval = 1000,
    expireTime = EXPIRE_TIMES.DAY,
    storage = 'local',
    clearOnUnmount = false,
    clearOnSubmit: _clearOnSubmit = false,
    onChange,
    onRestore,
    debug = false,
  } = options;

  // 存储键
  const storageKey = getFormStorageKey(formKey);
  
  // 状态
  const [data, setDataState] = useState<T>(() => {
    // 尝试从存储中恢复数据
    const saved = Persistence.get<SavedFormData<T>>(storageKey, { storage });
    if (saved?.data) {
      if (debug) {
        // 调试模式下保留分支，避免影响主流程
      }
      onRestore?.(saved.data);
      return saved.data;
    }
    return deepClone(initialValue);
  });

  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(() => {
    const saved = Persistence.get<SavedFormData<T>>(storageKey, { storage });
    return saved?.savedAt ? new Date(saved.savedAt) : null;
  });

  const [isDirty, setIsDirty] = useState(false);

  // 引用
  const initialValueRef = useRef(deepClone(initialValue));
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);

  // 检查是否有保存的数据
  const hasSavedData = Persistence.has(storageKey, { storage });

  // 保存数据到存储
  const saveToStorage = useCallback(
    (dataToSave: T) => {
      const savedData: SavedFormData<T> = {
        data: dataToSave,
        savedAt: Date.now(),
      };
      Persistence.set(storageKey, savedData, { storage, expire: expireTime });
      setLastSavedAt(new Date());
      setIsDirty(false);
      if (debug) {
        // 调试模式下保留分支，避免影响主流程
      }
    },
    [storageKey, storage, expireTime, debug]
  );

  // 设置数据
  const setData = useCallback(
    (newData: T | ((prev: T) => T)) => {
      setDataState((prev) => {
        const resolvedData = typeof newData === 'function'
          ? (newData as (prev: T) => T)(prev)
          : newData;
        
        // 检查是否与初始值相同
        const isDifferent = !deepEqual(resolvedData, initialValueRef.current);
        setIsDirty(isDifferent);

        // 触发变更回调
        onChange?.(resolvedData);

        // 设置自动保存
        if (autoSaveInterval > 0 && isDifferent) {
          if (saveTimeoutRef.current) {
            clearTimeout(saveTimeoutRef.current);
          }
          saveTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              saveToStorage(resolvedData);
            }
          }, autoSaveInterval);
        }

        return resolvedData;
      });
    },
    [autoSaveInterval, onChange, saveToStorage]
  );

  // 手动保存
  const save = useCallback(() => {
    saveToStorage(data);
  }, [data, saveToStorage]);

  // 清除保存的数据
  const clear = useCallback(() => {
    Persistence.remove(storageKey, { storage });
    setDataState(deepClone(initialValueRef.current));
    setLastSavedAt(null);
    setIsDirty(false);
    if (debug) {
      // 调试模式下保留分支，避免影响主流程
    }
  }, [storageKey, storage, debug]);

  // 重置为初始值
  const reset = useCallback(() => {
    setDataState(deepClone(initialValueRef.current));
    setIsDirty(false);
  }, []);

  // 恢复保存的数据
  const restore = useCallback(() => {
    const saved = Persistence.get<SavedFormData<T>>(storageKey, { storage });
    if (saved?.data) {
      setDataState(saved.data);
      setLastSavedAt(new Date(saved.savedAt));
      setIsDirty(!deepEqual(saved.data, initialValueRef.current));
      onRestore?.(saved.data);
      if (debug) {
        // 调试模式下保留分支，避免影响主流程
      }
    }
  }, [storageKey, storage, onRestore, debug]);

  // 组件卸载时的清理
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      
      // 清除待执行的保存定时器
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // 如果配置了卸载时清除，则清除数据
      if (clearOnUnmount) {
        Persistence.remove(storageKey, { storage });
        if (debug) {
          // 调试模式下保留分支，避免影响主流程
        }
      } else if (isDirty) {
        // 否则如果有修改，保存数据
        saveToStorage(data);
      }
    };
  }, [clearOnUnmount, storageKey, storage, isDirty, data, saveToStorage, formKey, debug]);

  // 更新初始值引用
  useEffect(() => {
    initialValueRef.current = deepClone(initialValue);
  }, [initialValue]);

  return {
    data,
    setData,
    reset,
    save,
    clear,
    hasSavedData,
    isDirty,
    lastSavedAt,
    restore,
  };
}

// ==================== useMultiFormPersistence Hook ====================

/**
 * 多表单持久化管理 Hook
 * 用于管理多个表单的持久化状态
 */
export function useMultiFormPersistence() {
  const formsRef = useRef<Map<string, { save: () => void; clear: () => void }>>(new Map());

  const register = useCallback((formKey: string, actions: { save: () => void; clear: () => void }) => {
    formsRef.current.set(formKey, actions);
  }, []);

  const unregister = useCallback((formKey: string) => {
    formsRef.current.delete(formKey);
  }, []);

  const saveAll = useCallback(() => {
    formsRef.current.forEach((form) => form.save());
  }, []);

  const clearAll = useCallback(() => {
    formsRef.current.forEach((form) => form.clear());
  }, []);

  return {
    register,
    unregister,
    saveAll,
    clearAll,
  };
}

// ==================== 工具函数导出 ====================

/**
 * 清除指定表单的保存数据
 */
export function clearFormData(formKey: string, storage: 'local' | 'session' = 'local'): void {
  Persistence.remove(getFormStorageKey(formKey), { storage });
}

/**
 * 清除所有表单保存的数据
 */
export function clearAllFormData(storage: 'local' | 'session' = 'local'): void {
  const storageObj = storage === 'local' ? localStorage : sessionStorage;
  const keysToRemove: string[] = [];

  for (let i = 0; i < storageObj.length; i++) {
    const key = storageObj.key(i);
    if (key?.startsWith('baixing_form_')) {
      keysToRemove.push(key);
    }
  }

  keysToRemove.forEach((key) => storageObj.removeItem(key));
}

/**
 * 获取所有已保存表单的键名列表
 */
export function getSavedFormKeys(storage: 'local' | 'session' = 'local'): string[] {
  const storageObj = storage === 'local' ? localStorage : sessionStorage;
  const keys: string[] = [];
  const prefix = 'baixing_form_';

  for (let i = 0; i < storageObj.length; i++) {
    const key = storageObj.key(i);
    if (key?.startsWith(prefix)) {
      keys.push(key.slice(prefix.length));
    }
  }

  return keys;
}

/**
 * 检查表单是否有保存的数据
 */
export function hasSavedFormData(formKey: string, storage: 'local' | 'session' = 'local'): boolean {
  return Persistence.has(getFormStorageKey(formKey), { storage });
}

export default useFormPersistence;