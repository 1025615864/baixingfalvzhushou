import { Input, Modal, Radio } from 'antd';

import type { ModerationQueueItem, ReviewAction } from '../types';

const { TextArea } = Input;

interface QuickReviewModalProps {
  visible: boolean;
  item?: ModerationQueueItem;
  action: ReviewAction;
  reason: string;
  note: string;
  submitting: boolean;
  onActionChange: (action: ReviewAction) => void;
  onReasonChange: (reason: string) => void;
  onNoteChange: (note: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

export function QuickReviewModal({
  visible,
  item,
  action,
  reason,
  note,
  submitting,
  onActionChange,
  onReasonChange,
  onNoteChange,
  onSubmit,
  onCancel,
}: QuickReviewModalProps): JSX.Element {
  return (
    <Modal
      title="确认审核操作"
      open={visible}
      onOk={onSubmit}
      onCancel={onCancel}
      confirmLoading={submitting}
      okText="确认"
      cancelText="取消"
      okButtonProps={{
        danger: action === 'reject',
      }}
    >
      {item && (
        <div>
          <p>
            <strong>内容类型：</strong>
            {item.contentType}
          </p>
          <p>
            <strong>内容摘要：</strong>
            {item.content.substring(0, 100)}
            {item.content.length > 100 ? '...' : ''}
          </p>
          <p>
            <strong>审核操作：</strong>
            <Radio.Group value={action} onChange={(e) => onActionChange(e.target.value as ReviewAction)}>
              <Radio value="approve">通过</Radio>
              <Radio value="reject">拒绝</Radio>
              <Radio value="escalate">升级</Radio>
            </Radio.Group>
          </p>
          <div style={{ marginTop: 16 }}>
            <p>审核原因（可选）：</p>
            <TextArea
              value={reason}
              onChange={(e) => onReasonChange(e.target.value)}
              placeholder="请输入审核原因，将通知用户"
              rows={3}
            />
          </div>
          <div style={{ marginTop: 16 }}>
            <p>内部备注（仅管理员可见）：</p>
            <TextArea
              value={note}
              onChange={(e) => onNoteChange(e.target.value)}
              placeholder="请输入内部备注"
              rows={2}
            />
          </div>
        </div>
      )}
    </Modal>
  );
}
