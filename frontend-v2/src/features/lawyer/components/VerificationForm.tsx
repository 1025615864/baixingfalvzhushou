/**
 * 律师认证申请表单组件
 * 用于律师提交资质认证申请
 */

import React, { useState } from 'react';

import type { SubmitVerificationRequest } from '../types';
import { useSubmitVerification } from '../hooks/useVerification';

interface VerificationFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface FormErrors {
  realName?: string;
  idCardNo?: string;
  licenseNo?: string;
  firmName?: string;
}

export const VerificationForm: React.FC<VerificationFormProps> = ({
  onSuccess,
  onCancel,
}) => {
  const [formData, setFormData] = useState<SubmitVerificationRequest>({
    realName: '',
    idCardNo: '',
    licenseNo: '',
    firmName: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [idCardFront, setIdCardFront] = useState<File | null>(null);
  const [idCardBack, setIdCardBack] = useState<File | null>(null);
  const [licensePhoto, setLicensePhoto] = useState<File | null>(null);

  const submitMutation = useSubmitVerification();

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.realName.trim()) {
      newErrors.realName = '请输入真实姓名';
    }

    if (!formData.idCardNo.trim()) {
      newErrors.idCardNo = '请输入身份证号';
    } else if (!/^\d{17}[\dXx]$/.test(formData.idCardNo)) {
      newErrors.idCardNo = '身份证号格式不正确';
    }

    if (!formData.licenseNo.trim()) {
      newErrors.licenseNo = '请输入执业证号';
    }

    if (!formData.firmName.trim()) {
      newErrors.firmName = '请输入所属律所';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    void submitMutation.mutateAsync(formData).then(() => {
      onSuccess?.();
    }).catch(() => {
      // 错误由 mutation 处理
    });
  };

  const handleChange = (field: keyof SubmitVerificationRequest, value: string) => {
    if (field === 'experienceYears') {
      const numValue = value === '' ? undefined : Number(value);
      setFormData(prev => ({ ...prev, experienceYears: numValue }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    setter: React.Dispatch<React.SetStateAction<File | null>>
  ) => {
    const file = e.target.files?.[0];
    if (file) {
      setter(file);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">律师认证申请</h2>
        <p className="text-sm text-gray-500 mb-6">
          请填写真实信息并上传相关证件照片，审核通过后即可成为认证律师。
        </p>
      </div>

      {/* 真实姓名 */}
      <div>
        <label htmlFor="realName" className="block text-sm font-medium text-gray-700">
          真实姓名 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="realName"
          value={formData.realName}
          onChange={e => handleChange('realName', e.target.value)}
          className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
            errors.realName
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }`}
          placeholder="请输入您的真实姓名"
        />
        {errors.realName && (
          <p className="mt-1 text-sm text-red-600">{errors.realName}</p>
        )}
      </div>

      {/* 身份证号 */}
      <div>
        <label htmlFor="idCardNo" className="block text-sm font-medium text-gray-700">
          身份证号 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="idCardNo"
          value={formData.idCardNo}
          onChange={e => handleChange('idCardNo', e.target.value)}
          maxLength={18}
          className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
            errors.idCardNo
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }`}
          placeholder="请输入18位身份证号"
        />
        {errors.idCardNo && (
          <p className="mt-1 text-sm text-red-600">{errors.idCardNo}</p>
        )}
      </div>

      {/* 执业证号 */}
      <div>
        <label htmlFor="licenseNo" className="block text-sm font-medium text-gray-700">
          执业证号 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="licenseNo"
          value={formData.licenseNo}
          onChange={e => handleChange('licenseNo', e.target.value)}
          className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
            errors.licenseNo
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }`}
          placeholder="请输入律师执业证号"
        />
        {errors.licenseNo && (
          <p className="mt-1 text-sm text-red-600">{errors.licenseNo}</p>
        )}
      </div>

      {/* 所属律所 */}
      <div>
        <label htmlFor="firmName" className="block text-sm font-medium text-gray-700">
          所属律所 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="firmName"
          value={formData.firmName}
          onChange={e => handleChange('firmName', e.target.value)}
          className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
            errors.firmName
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }`}
          placeholder="请输入所属律师事务所名称"
        />
        {errors.firmName && (
          <p className="mt-1 text-sm text-red-600">{errors.firmName}</p>
        )}
      </div>

      {/* 专业领域 */}
      <div>
        <label htmlFor="specialties" className="block text-sm font-medium text-gray-700">
          专业领域
        </label>
        <input
          type="text"
          id="specialties"
          value={formData.specialties || ''}
          onChange={e => handleChange('specialties', e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="如：民商事诉讼、刑事辩护、知识产权等"
        />
      </div>

      {/* 执业年限 */}
      <div>
        <label htmlFor="experienceYears" className="block text-sm font-medium text-gray-700">
          执业年限
        </label>
        <input
          type="number"
          id="experienceYears"
          value={formData.experienceYears || ''}
          onChange={e => handleChange('experienceYears', e.target.value)}
          min={0}
          max={50}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="请输入执业年限"
        />
      </div>

      {/* 个人简介 */}
      <div>
        <label htmlFor="introduction" className="block text-sm font-medium text-gray-700">
          个人简介
        </label>
        <textarea
          id="introduction"
          value={formData.introduction || ''}
          onChange={e => handleChange('introduction', e.target.value)}
          rows={4}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="请简要介绍您的执业经历和专业特长"
        />
      </div>

      {/* 身份证照片上传 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            身份证正面
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
            <div className="space-y-1 text-center">
              {idCardFront ? (
                <p className="text-sm text-gray-600">{idCardFront.name}</p>
              ) : (
                <>
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="idCardFront"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                    >
                      <span>上传文件</span>
                      <input
                        id="idCardFront"
                        name="idCardFront"
                        type="file"
                        accept="image/*"
                        className="sr-only"
                        onChange={e => handleFileChange(e, setIdCardFront)}
                      />
                    </label>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            身份证背面
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
            <div className="space-y-1 text-center">
              {idCardBack ? (
                <p className="text-sm text-gray-600">{idCardBack.name}</p>
              ) : (
                <>
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="idCardBack"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                    >
                      <span>上传文件</span>
                      <input
                        id="idCardBack"
                        name="idCardBack"
                        type="file"
                        accept="image/*"
                        className="sr-only"
                        onChange={e => handleFileChange(e, setIdCardBack)}
                      />
                    </label>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 执业证照片 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          执业证照片
        </label>
        <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
          <div className="space-y-1 text-center">
            {licensePhoto ? (
              <p className="text-sm text-gray-600">{licensePhoto.name}</p>
            ) : (
              <>
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="flex text-sm text-gray-600">
                  <label
                    htmlFor="licensePhoto"
                    className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                  >
                    <span>上传文件</span>
                    <input
                      id="licensePhoto"
                      name="licensePhoto"
                      type="file"
                      accept="image/*"
                      className="sr-only"
                      onChange={e => handleFileChange(e, setLicensePhoto)}
                    />
                  </label>
                </div>
                <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 提交按钮 */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            取消
          </button>
        )}
        <button
          type="submit"
          disabled={submitMutation.isPending}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitMutation.isPending ? '提交中...' : '提交申请'}
        </button>
      </div>

      {/* 错误提示 */}
      {submitMutation.isError && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {submitMutation.error?.message || '提交失败，请重试'}
              </h3>
            </div>
          </div>
        </div>
      )}
    </form>
  );
};

export default VerificationForm;