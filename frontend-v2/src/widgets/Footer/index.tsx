/**
 * Footer 组件 - 页脚
 * 百姓助手法律服务平台页脚
 */

import { Link } from 'react-router-dom';
import {
  Scale,
  Mail,
  Phone,
  MapPin,
  Shield,
  Award,
  Clock,
} from 'lucide-react';

const footerLinks = {
  services: [
    { label: 'AI智能咨询', href: '/chat' },
    { label: '找律师', href: '/lawyer' },
    { label: '法律知识库', href: '/knowledge' },
    { label: '合同审查', href: '/contracts' },
    { label: '文书生成', href: '/document' },
    { label: '费用计算', href: '/calculator' },
  ],
  resources: [
    { label: '帮助中心', href: '/help' },
    { label: '常见问题', href: '/faq' },
    { label: '法律资讯', href: '/news' },
    { label: '案例分享', href: '/knowledge' }, // 重定向到知识库
    { label: '法律法规', href: '/knowledge' }, // 重定向到知识库
    // { label: '普法课堂', href: '/courses' }, // 暂时移除，待功能上线
  ],
  about: [
    { label: '关于我们', href: '/about' },
    // { label: '加入我们', href: '/careers' }, // 暂时移除，待功能上线
    // { label: '合作伙伴', href: '/partners' }, // 暂时移除，待功能上线
    { label: '联系方式', href: '/contact' },
    { label: '意见反馈', href: '/feedback' },
    { label: '投诉建议', href: '/feedback' }, // 重定向到意见反馈
  ],
  legal: [
    { label: '用户协议', href: '/terms' },
    { label: '隐私政策', href: '/privacy' },
    { label: 'AI免责声明', href: '/terms' }, // 合并到用户协议
    { label: 'Cookie政策', href: '/privacy' }, // 合并到隐私政策
  ],
};

const socialLinks = [
  { icon: Scale, label: '微信公众号', href: '#' },
  { icon: Shield, label: '微博', href: '#' },
];

const certifications = [
  { icon: Shield, label: 'ISO 27001认证' },
  { icon: Award, label: '国家高新技术企业' },
  { icon: Clock, label: '7×24小时服务' },
];

export function Footer(): JSX.Element {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-900 text-slate-300">
      {/* 信任徽章区域 */}
      <div className="border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {certifications.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-center gap-3 p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-slate-600 transition-colors"
              >
                <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center">
                  <item.icon className="w-5 h-5 text-primary-400" />
                </div>
                <span className="font-medium text-slate-200">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 lg:grid-cols-6 gap-8 lg:gap-12">
          {/* 品牌信息 */}
          <div className="lg:col-span-2">
            <Link to="/" className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-hero rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
                <Scale className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold text-white">
                  <span className="text-primary-400">百姓</span>助手
                </span>
                <p className="text-xs text-slate-500">专业法律服务平台</p>
              </div>
            </Link>
            <p className="text-sm text-slate-400 leading-relaxed mb-6">
              百姓助手致力于让每个人都能获得专业、便捷、可信赖的法律服务。
              我们运用先进的人工智能技术，连接优质律师资源，为您提供全方位的法律解决方案。
            </p>

            {/* 联系方式 */}
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <Phone className="w-4 h-4 text-primary-400" />
                <span>400-888-8888</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Mail className="w-4 h-4 text-primary-400" />
                <span>service@baixing.com</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <MapPin className="w-4 h-4 text-primary-400" />
                <span>北京市朝阳区建国路88号</span>
              </div>
            </div>

            {/* 社交媒体 */}
            <div className="flex items-center gap-4 mt-6">
              {socialLinks.map((social, index) => (
                <a
                  key={index}
                  href={social.href}
                  className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center hover:bg-primary-600 transition-colors group"
                  aria-label={social.label}
                >
                  <social.icon className="w-5 h-5 text-slate-400 group-hover:text-white" />
                </a>
              ))}
            </div>
          </div>

          {/* 链接区域 */}
          <div className="lg:col-span-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {/* 服务项目 */}
              <div>
                <h3 className="text-sm font-semibold text-white mb-4">服务项目</h3>
                <ul className="space-y-3">
                  {footerLinks.services.map((link) => (
                    <li key={link.href}>
                      <Link
                        to={link.href}
                        className="text-sm text-slate-400 hover:text-primary-400 transition-colors"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 学习资源 */}
              <div>
                <h3 className="text-sm font-semibold text-white mb-4">学习资源</h3>
                <ul className="space-y-3">
                  {footerLinks.resources.map((link) => (
                    <li key={link.href}>
                      <Link
                        to={link.href}
                        className="text-sm text-slate-400 hover:text-primary-400 transition-colors"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 关于我们 */}
              <div>
                <h3 className="text-sm font-semibold text-white mb-4">关于我们</h3>
                <ul className="space-y-3">
                  {footerLinks.about.map((link) => (
                    <li key={link.href}>
                      <Link
                        to={link.href}
                        className="text-sm text-slate-400 hover:text-primary-400 transition-colors"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 法律条款 */}
              <div>
                <h3 className="text-sm font-semibold text-white mb-4">法律条款</h3>
                <ul className="space-y-3">
                  {footerLinks.legal.map((link) => (
                    <li key={link.href}>
                      <Link
                        to={link.href}
                        className="text-sm text-slate-400 hover:text-primary-400 transition-colors"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 法律免责声明 */}
      <div className="border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-xs text-slate-500 text-center leading-relaxed">
            免责声明：百姓助手提供的AI咨询服务仅供参考，不构成法律意见。如有具体法律问题，请咨询专业律师。
            我们不对因使用本平台服务而产生的任何损失承担责任。
          </p>
        </div>
      </div>

      {/* 版权信息 */}
      <div className="border-t border-slate-800 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-500">
              © {currentYear} 百姓助手. 保留所有权利.
            </p>
            <div className="flex items-center gap-6 text-xs text-slate-500">
              <span>京ICP备12345678号-1</span>
              <span>京公网安备 11010502000000号</span>
              <span>增值电信业务经营许可证</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
