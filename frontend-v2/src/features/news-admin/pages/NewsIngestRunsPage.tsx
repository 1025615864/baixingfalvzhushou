/**
 * News Ingest Runs Page
 * 采集运行记录页面
 */

import { NewsIngestRunList } from '../components/NewsIngestRunList';

export function NewsIngestRunsPage(): JSX.Element {
  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">采集运行记录</h1>
        <p className="text-slate-600 mt-1">查看每次 RSS 抓取的运行状态与统计</p>
      </div>
      <NewsIngestRunList />
    </div>
  );
}
