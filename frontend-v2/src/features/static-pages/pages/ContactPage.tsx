/**
 * 联系方式页面
 * 百姓助手法律服务平台联系方式
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Phone,
  Mail,
  MapPin,
  Clock,
  MessageSquare,
  Send,
  Building2,
  HelpCircle,
} from 'lucide-react';

interface QuickLinkItem {
  icon: React.ElementType;
  label: string;
  href: string;
}

const contactChannels = [
  {
    icon: Phone,
    title: '客服热线',
    description: '7×24小时服务',
    content: '400-888-8888',
    action: 'tel:400-888-8888',
    actionLabel: '立即拨打',
  },
  {
    icon: Mail,
    title: '商务合作',
    description: '工作日24小时内回复',
    content: 'business@baixing.com',
    action: 'mailto:business@baixing.com',
    actionLabel: '发送邮件',
  },
  {
    icon: Mail,
    title: '客服邮箱',
    description: '工作日24小时内回复',
    content: 'service@baixing.com',
    action: 'mailto:service@baixing.com',
    actionLabel: '发送邮件',
  },
  {
    icon: MessageSquare,
    title: '在线客服',
    description: '即时在线沟通',
    content: '点击开始对话',
    action: '/chat',
    actionLabel: '开始对话',
  },
];

const officeLocations = [
  {
    city: '北京总部',
    address: '北京市朝阳区建国路88号SOHO现代城A座18层',
    phone: '010-88888888',
    hours: '周一至周五 9:00-18:00',
  },
  {
    city: '上海分部',
    address: '上海市浦东新区陆家嘴环路1000号恒生银行大厦12层',
    phone: '021-88888888',
    hours: '周一至周五 9:00-18:00',
  },
  {
    city: '深圳分部',
    address: '深圳市南山区科技园南区深南大道9966号威盛科技大厦8层',
    phone: '0755-88888888',
    hours: '周一至周五 9:00-18:00',
  },
];

const faqs = [
  {
    question: '如何选择合适的律师？',
    answer: '您可以通过我们的智能匹配系统，根据您的法律需求和预算，系统会为您推荐最合适的律师。您也可以查看律师的专业领域、评价和案例经验来做出选择。',
  },
  {
    question: 'AI咨询服务是免费的吗？',
    answer: '我们提供基础的AI智能咨询服务是免费的。如果您需要更深入的法律意见或专业律师服务，可以选择付费服务套餐。',
  },
  {
    question: '如何保障我的隐私安全？',
    answer: '我们严格遵守相关法律法规，采用银行级加密技术保护您的个人信息。所有咨询服务均采用端到端加密，确保您的隐私安全。',
  },
  {
    question: '对服务不满意怎么办？',
    answer: '如果您对我们的服务不满意，可以通过意见反馈或投诉渠道向我们反映。我们承诺在24小时内响应，并尽快为您解决问题。',
  },
];

const quickLinks: QuickLinkItem[] = [
  { icon: HelpCircle, label: '帮助中心', href: '/help' },
  { icon: MessageSquare, label: '常见问题', href: '/faq' },
  { icon: MessageSquare, label: '意见反馈', href: '/feedback' },
  { icon: Building2, label: '关于我们', href: '/about' },
];

export function ContactPage(): JSX.Element {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // 模拟提交
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitSuccess(true);
      setFormData({ name: '', phone: '', email: '', subject: '', message: '' });
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-50" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">联系我们</h1>
            <p className="text-xl text-primary-100 max-w-2xl mx-auto">
              我们随时准备为您提供帮助，选择最适合您的联系方式
            </p>
          </div>
        </div>
      </section>

      {/* Contact Channels */}
      <section className="relative -mt-8 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {contactChannels.map((channel, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
                  <channel.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-1">{channel.title}</h3>
                <p className="text-sm text-slate-500 mb-3">{channel.description}</p>
                <p className="text-primary-600 font-medium mb-4">{channel.content}</p>
                {channel.action.startsWith('/') ? (
                  <Link
                    to={channel.action}
                    className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {channel.actionLabel}
                    <Send className="w-4 h-4 ml-1" />
                  </Link>
                ) : (
                  <a
                    href={channel.action}
                    className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {channel.actionLabel}
                    <Send className="w-4 h-4 ml-1" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Form & Map */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact Form */}
            <div className="bg-white rounded-2xl p-8 shadow-lg">
              <h2 className="text-2xl font-bold text-slate-900 mb-6">在线留言</h2>
              {submitSuccess ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Send className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">提交成功！</h3>
                  <p className="text-slate-600 mb-6">我们会在24小时内与您联系</p>
                  <button
                    onClick={() => setSubmitSuccess(false)}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    继续留言
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        姓名 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all"
                        placeholder="请输入您的姓名"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        手机号 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="tel"
                        required
                        value={formData.phone}
                        onChange={e => setFormData({ ...formData, phone: e.target.value })}
                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all"
                        placeholder="请输入您的手机号"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">邮箱</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={e => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all"
                      placeholder="请输入您的邮箱"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      主题 <span className="text-red-500">*</span>
                    </label>
                    <select
                      required
                      value={formData.subject}
                      onChange={e => setFormData({ ...formData, subject: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all"
                    >
                      <option value="">请选择主题</option>
                      <option value="service">服务咨询</option>
                      <option value="cooperation">商务合作</option>
                      <option value="complaint">投诉建议</option>
                      <option value="technical">技术问题</option>
                      <option value="other">其他</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      留言内容 <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      required
                      rows={5}
                      value={formData.message}
                      onChange={e => setFormData({ ...formData, message: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all resize-none"
                      placeholder="请详细描述您的问题或需求..."
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? '提交中...' : '提交留言'}
                  </button>
                </form>
              )}
            </div>

            {/* Quick Links & Social */}
            <div className="space-y-8">
              {/* Quick Links */}
              <div className="bg-white rounded-2xl p-8 shadow-lg">
                <h2 className="text-2xl font-bold text-slate-900 mb-6">快速入口</h2>
                <div className="grid grid-cols-2 gap-4">
                  {quickLinks.map((item, index) => (
                    <Link
                      key={index}
                      to={item.href}
                      className="flex items-center gap-3 p-4 bg-slate-50 rounded-xl hover:bg-primary-50 transition-colors group"
                    >
                      <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                        <item.icon className="w-5 h-5 text-primary-600" />
                      </div>
                      <span className="font-medium text-slate-700">{item.label}</span>
                    </Link>
                  ))}
                </div>
              </div>

              {/* QR Code */}
              <div className="bg-white rounded-2xl p-8 shadow-lg">
                <h2 className="text-2xl font-bold text-slate-900 mb-6">关注我们</h2>
                <div className="flex items-center gap-8">
                  <div className="text-center">
                    <div className="w-32 h-32 bg-slate-100 rounded-xl flex items-center justify-center mb-2">
                      <MessageSquare className="w-16 h-16 text-green-500" />
                    </div>
                    <p className="text-sm text-slate-600">微信公众号</p>
                  </div>
                  <div className="text-center">
                    <div className="w-32 h-32 bg-slate-100 rounded-xl flex items-center justify-center mb-2">
                      <MessageSquare className="w-16 h-16 text-green-500" />
                    </div>
                    <p className="text-sm text-slate-600">客服微信</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Office Locations */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">办公地址</h2>
            <p className="text-lg text-slate-600">欢迎来访，请提前预约</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {officeLocations.map((office, index) => (
              <div
                key={index}
                className="p-6 bg-slate-50 rounded-2xl hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-primary-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">{office.city}</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-600">{office.address}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Phone className="w-5 h-5 text-slate-400" />
                    <span className="text-slate-600">{office.phone}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Clock className="w-5 h-5 text-slate-400" />
                    <span className="text-slate-600">{office.hours}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">常见问题</h2>
            <p className="text-lg text-slate-600">快速解答您的疑惑</p>
          </div>
          <div className="max-w-3xl mx-auto space-y-4">
            {faqs.map((faq, index) => (
              <details
                key={index}
                className="bg-white rounded-xl shadow-sm group"
              >
                <summary className="flex items-center justify-between p-6 cursor-pointer list-none">
                  <span className="font-medium text-slate-900">{faq.question}</span>
                  <span className="text-primary-600 group-open:rotate-180 transition-transform">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </summary>
                <div className="px-6 pb-6 text-slate-600">{faq.answer}</div>
              </details>
            ))}
          </div>
          <div className="text-center mt-8">
            <Link
              to="/faq"
              className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium"
            >
              查看更多问题
              <Send className="w-4 h-4 ml-1" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}