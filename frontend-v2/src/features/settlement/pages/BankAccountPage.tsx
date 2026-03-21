/**
 * BankAccountPage - 银行卡管理页面
 * 
 * 功能：银行卡列表、添加银行卡、编辑删除
 */

import { useState } from 'react';

import { useBankAccounts, useAddBankAccount, useDeleteBankAccount, useSetDefaultBankAccount } from '../hooks/useSettlements';
import { useToast } from '../../../components/ui/useToast';
import type { AccountType, BankAccount } from '../types';

/**
 * 账户类型配置
 */
const accountTypeConfig: Record<AccountType, { label: string; icon: string }> = {
  personal: { label: '个人账户', icon: '👤' },
  corporate: { label: '企业账户', icon: '🏢' },
};

/**
 * 银行卡卡片组件
 */
function BankAccountCard({
  account,
  isDefault,
  onSetDefault,
  onDelete,
}: {
  account: BankAccount;
  isDefault: boolean;
  onSetDefault: () => void;
  onDelete: () => void;
}): JSX.Element {
  const accountType = account.accountType as AccountType;

  return (
    <div
      className={`bg-white rounded-xl shadow-sm p-6 border-2 ${
        isDefault ? 'border-blue-500' : 'border-transparent'
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{accountTypeConfig[accountType]?.icon || '🏦'}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {account.bankName || '银行卡'}
            </h3>
            <p className="text-sm text-gray-500">{accountTypeConfig[accountType]?.label}</p>
          </div>
        </div>
        {isDefault && (
          <span className="px-3 py-1 bg-blue-100 text-blue-600 text-xs font-medium rounded-full">
            默认账户
          </span>
        )}
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex items-center gap-2 text-gray-600">
          <span className="text-sm">卡号：</span>
          <span className="font-mono text-lg">{account.accountNo}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <span className="text-sm">持卡人：</span>
          <span>{account.accountHolder}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <span className="text-sm">添加时间：</span>
          <span className="text-sm">
            {new Date(account.createdAt).toLocaleDateString('zh-CN')}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-4 border-t">
        {!isDefault && (
          <button
            onClick={onSetDefault}
            className="flex-1 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-100 transition-colors"
          >
            设为默认
          </button>
        )}
        <button
          onClick={onDelete}
          className="flex-1 px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors"
        >
          删除
        </button>
      </div>
    </div>
  );
}

/**
 * 添加银行卡表单
 */
function AddBankAccountForm({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }): JSX.Element {
  const addBankAccount = useAddBankAccount();
  const toast = useToast();

  const [accountType, setAccountType] = useState<AccountType>('personal');
  const [bankName, setBankName] = useState('');
  const [accountNo, setAccountNo] = useState('');
  const [accountHolder, setAccountHolder] = useState('');
  const [isDefault, setIsDefault] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 验证表单
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!bankName.trim()) {
      newErrors.bankName = '请输入银行名称';
    }

    if (!accountNo.trim()) {
      newErrors.accountNo = '请输入银行卡号';
    } else if (accountNo.replace(/\s/g, '').length < 16) {
      newErrors.accountNo = '银行卡号格式不正确';
    }

    if (!accountHolder.trim()) {
      newErrors.accountHolder = '请输入持卡人姓名';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 提交表单
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!validate()) return;

    try {
      await addBankAccount.mutateAsync({
        accountType,
        bankName: bankName.trim(),
        accountNo: accountNo.replace(/\s/g, ''),
        accountHolder: accountHolder.trim(),
        isDefault,
      });

      toast.success('银行卡添加成功');
      onSuccess();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '添加失败');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">添加银行卡</h2>

        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          {/* 账户类型 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              账户类型
            </label>
            <div className="grid grid-cols-2 gap-3">
              {(['personal', 'corporate'] as AccountType[]).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setAccountType(type)}
                  className={`p-3 border rounded-lg text-center transition-all ${
                    accountType === type
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-xl">{accountTypeConfig[type].icon}</span>
                  <span className="block text-sm mt-1">{accountTypeConfig[type].label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 银行名称 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              银行名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={bankName}
              onChange={(e) => setBankName(e.target.value)}
              placeholder="例如：中国工商银行"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.bankName ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.bankName && <p className="mt-1 text-sm text-red-600">{errors.bankName}</p>}
          </div>

          {/* 银行卡号 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              银行卡号 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={accountNo}
              onChange={(e) => setAccountNo(e.target.value)}
              placeholder="请输入银行卡号"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.accountNo ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.accountNo && <p className="mt-1 text-sm text-red-600">{errors.accountNo}</p>}
          </div>

          {/* 持卡人姓名 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              持卡人姓名 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={accountHolder}
              onChange={(e) => setAccountHolder(e.target.value)}
              placeholder="请输入持卡人姓名"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.accountHolder ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.accountHolder && (
              <p className="mt-1 text-sm text-red-600">{errors.accountHolder}</p>
            )}
          </div>

          {/* 设为默认 */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isDefault"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="isDefault" className="text-sm text-gray-700">
              设为默认收款账户
            </label>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={addBankAccount.isPending}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {addBankAccount.isPending ? '添加中...' : '确认添加'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * 空状态提示
 */
function EmptyState({ onAdd }: { onAdd: () => void }): JSX.Element {
  return (
    <div className="bg-white rounded-xl shadow-sm p-12 text-center">
      <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <span className="text-4xl">🏦</span>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">暂无银行卡</h3>
      <p className="text-gray-500 mb-6">添加您的第一张银行卡，用于接收提现款项</p>
      <button
        onClick={onAdd}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        添加银行卡
      </button>
    </div>
  );
}

/**
 * 银行卡管理页面
 */
export function BankAccountPage(): JSX.Element {
  const { data: accounts, isLoading, refetch } = useBankAccounts();
  const deleteBankAccount = useDeleteBankAccount();
  const setDefaultBankAccount = useSetDefaultBankAccount();
  const toast = useToast();

  const [showAddForm, setShowAddForm] = useState(false);

  // 设置默认账户
  const handleSetDefault = async (accountId: string): Promise<void> => {
    try {
      await setDefaultBankAccount.mutateAsync(accountId);
      toast.success('已设为默认账户');
      void refetch();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '设置失败');
    }
  };

  // 删除账户
  const handleDelete = async (accountId: string): Promise<void> => {
    if (!window.confirm('确定要删除这张银行卡吗？此操作不可恢复。')) {
      return;
    }

    try {
      await deleteBankAccount.mutateAsync(accountId);
      toast.success('银行卡已删除');
      void refetch();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '删除失败');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">银行卡管理</h1>
            <p className="text-gray-500 mt-1">管理您的收款银行卡账户</p>
          </div>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            + 添加银行卡
          </button>
        </div>

        {/* 提示说明 */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <span className="text-xl">💡</span>
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">温馨提示</p>
              <ul className="space-y-1 text-blue-700">
                <li>• 您需要至少绑定一张银行卡才能进行提现</li>
                <li>• 默认账户将作为提现的默认收款账户</li>
                <li>• 请确保银行卡信息准确无误，以免影响提现到账</li>
                <li>• 如需修改银行卡信息，请先删除后重新添加</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 银行卡列表 */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="space-y-3 mb-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                </div>
                <div className="h-10 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
        ) : !accounts || accounts.length === 0 ? (
          <EmptyState onAdd={() => setShowAddForm(true)} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {accounts.map((account) => (
              <BankAccountCard
                key={account.id}
                account={account}
                isDefault={account.isDefault}
                onSetDefault={() => void handleSetDefault(account.id)}
                onDelete={() => void handleDelete(account.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* 添加银行卡表单 */}
      {showAddForm && (
        <AddBankAccountForm
          onSuccess={() => {
            setShowAddForm(false);
            void refetch();
          }}
          onCancel={() => setShowAddForm(false)}
        />
      )}
    </div>
  );
}