/**
 * Points Feature - Components Index
 *
 * 导出积分功能相关的所有组件
 */

// 积分余额组件
export { PointsBalance } from './PointsBalance';
export type { PointsBalanceProps } from './PointsBalance';

// 签到日历组件
export { CheckInCalendar } from './CheckInCalendar';
export type { CheckInCalendarProps } from './CheckInCalendar';

// 签到成功动画组件
export {
  CheckInSuccessAnimation,
  useCheckInSuccessAnimation,
} from './CheckInSuccessAnimation';

// 积分历史列表组件
export { PointsHistoryList } from './PointsHistoryList';
export type { PointsHistoryItem } from './PointsHistoryList';

// 积分任务指南组件
export { PointsTaskGuide } from './PointsTaskGuide';