/**
 * 帮助中心页面
 * 百姓助手法律服务平台帮助中心
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  MessageSquare,
  Phone,
  Mail,
  BookOpen,
  FileText,
  Scale,
  Users,
  CreditCard,
  Shield,
  Settings,
  ChevronRight,
  HelpCircle,
} from 'lucide-react';

const categories = [
  {
    icon: MessageSquare,
    title: 'AI咨询',
    description: '关于AI智能咨询的使用问题',
    href: '#ai-consultation',
  },
  {
    icon: Scale,
    title: '律师服务',
    description: '律师咨询、预约相关问题',
    href: '#lawyer-service',
  },
  {
    icon: FileText,
    title: '文书服务',
    description: '法律文书生成与合同审查',
    href: '#document-service',
  },
  {
    icon: CreditCard,
    title: '账户与支付',
    description: '账户管理、支付相关问题',
    href: '#account-payment',
  },
  {
    icon: Shield,
    title: '隐私与安全',
    description: '隐私保护、账户安全问题',
    href: '#privacy-security',
  },
  {
    icon: Settings,
    title: '其他问题',
    description: '更多常见问题解答',
    href: '#other',
  },
];

const faqData: Record<string, { question: string; answer: string }[]> = {
  'ai-consultation': [
    {
      question: 'AI咨询是免费的吗？',
      answer: '我们提供基础的AI智能咨询服务是免费的。如果您需要更深入的法律意见或专业律师服务，可以选择付费服务套餐。',
    },
    {
      question: 'AI咨询的结果准确吗？',
      answer: 'AI咨询基于大量法律数据训练，能够提供参考性的法律信息。但请注意，AI咨询结果仅供参考，不构成正式的法律意见。对于复杂或重大法律问题，建议咨询专业律师。',
    },
    {
      question: '如何获得更好的咨询效果？',
      answer: '建议您在咨询时尽可能详细地描述问题背景，包括相关的时间、地点、人物等信息。这样AI能够更好地理解您的情况，提供更有针对性的建议。',
    },
    {
      question: 'AI咨询记录会被保存吗？',
      answer: '是的，您的咨询记录会被保存在您的账户中，方便您随时查看历史对话。我们会对您的隐私信息进行严格保护。',
    },
  ],
  'lawyer-service': [
    {
      question: '如何选择合适的律师？',
      answer: '您可以通过我们的智能匹配系统，根据您的法律需求和预算，系统会为您推荐最合适的律师。您也可以查看律师的专业领域、评价和案例经验来做出选择。',
    },
    {
      question: '律师咨询如何收费？',
      answer: '律师咨询的收费标准由律师自行设定，不同律师、不同案件的收费可能不同。您可以在律师详情页面查看其收费标准，也可以在咨询前与律师确认费用。',
    },
    {
      question: '如何预约律师咨询？',
      answer: '在律师详情页面点击"预约咨询"按钮，选择您方便的时间段，填写咨询问题描述，完成支付后即可预约成功。',
    },
    {
      question: '对律师服务不满意怎么办？',
      answer: '如果您对律师服务不满意，可以在咨询结束后进行评价和反馈。如有重大问题，可以联系客服进行投诉，我们会尽快处理。',
    },
  ],
  'document-service': [
    {
      question: '如何生成法律文书？',
      answer: '进入"文书生成"页面，选择您需要的文书类型，按照提示填写相关信息，系统会自动生成符合规范的法律文书。',
    },
    {
      question: '合同审查需要多长时间？',
      answer: 'AI合同审查通常在几分钟内即可完成。如果您选择律师人工审查，通常需要1-3个工作日，具体时间视合同复杂程度而定。',
    },
    {
      question: '生成的文书有法律效力吗？',
      answer: '我们生成的文书符合相关法律规范，但建议您在使用前咨询专业律师，确保文书内容完全符合您的具体需求和当地法律规定。',
    },
    {
      question: '如何下载生成的文书？',
      answer: '文书生成后，您可以选择PDF或Word格式下载。下载按钮在文书预览页面的右上角。',
    },
  ],
  'account-payment': [
    {
      question: '如何注册账户？',
      answer: '点击页面右上角的"注册"按钮，您可以使用手机号或邮箱进行注册。按照提示完成验证即可。',
    },
    {
      question: '忘记密码怎么办？',
      answer: '在登录页面点击"忘记密码"，输入您的注册手机号或邮箱，按照提示重置密码。',
    },
    {
      question: '支持哪些支付方式？',
      answer: '我们支持微信支付、支付宝、银行卡等多种支付方式。具体可用方式以支付页面显示为准。',
    },
    {
      question: '如何申请退款？',
      answer: '部分服务支持退款，具体规则请查看服务说明。如需退款，请联系客服说明情况，我们会在核实后处理。',
    },
    {
      question: '如何查看我的订单？',
      answer: '登录后点击右上角的头像，选择"我的订单"即可查看所有订单记录。',
    },
  ],
  'privacy-security': [
    {
      question: '我的个人信息安全吗？',
      answer: '我们采用银行级加密技术保护您的个人信息，所有数据传输和存储都经过加密处理。详情请查看我们的《隐私政策》。',
    },
    {
      question: '如何修改个人信息？',
      answer: '登录后进入"个人中心" > "账户设置"，可以修改您的基本信息。部分敏感信息修改可能需要验证身份。',
    },
    {
      question: '如何注销账户？',
      answer: '如需注销账户，请联系客服申请。注销后您的个人信息将被删除或匿名化处理。',
    },
    {
      question: '发现账户被盗怎么办？',
      answer: '请立即修改密码并联系客服。建议您开启二次验证功能，增强账户安全性。',
    },
  ],
  'other': [
    {
      question: '平台的服务时间？',
      answer: 'AI咨询服务24小时在线。人工客服服务时间为工作日9:00-18:00。律师服务时间以律师个人安排为准。',
    },
    {
      question: '如何成为平台律师？',
      answer: '如果您是执业律师，可以在"律师入驻"页面提交申请。我们需要审核您的执业资质，审核通过后即可在平台提供服务。',
    },
    {
      question: '如何投诉或建议？',
      answer: '您可以通过"意见反馈"页面提交投诉或建议，也可以拨打客服热线400-888-8888。',
    },
  ],
};

const contactOptions = [
  {
    icon: Phone,
    title: '客服热线',
    content: '400-888-8888',
    description: '工作日 9:00-18:00',
    action: 'tel:400-888-8888',
  },
  {
    icon: Mail,
    title: '邮箱',
    content: 'service@baixing.com',
    description: '24小时内回复',
    action: 'mailto:service@baixing.com',
  },
  {
    icon: MessageSquare,
    title: '在线客服',
    content: '立即对话',
    description: 'AI智能客服',
    action: '/chat',
  },
];

export function HelpPage(): JSX.Element {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedQuestions, setExpandedQuestions] = useState<Record<string, boolean>>({});

  const toggleQuestion = (key: string) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const filterFAQs = (question: string) => {
    if (!searchQuery) return true;
    return question.toLowerCase().includes(searchQuery.toLowerCase());
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full text-sm font-medium mb-6">
              <HelpCircle className="w-4 h-4" />
              <span>帮助中心</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-6">有什么可以帮助您？</h1>
            <div className="relative max-w-xl mx-auto">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="搜索问题..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 rounded-2xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-white/20"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="relative -mt-6 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">常见问题分类</h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((category, index) => (
                <a
                  key={index}
                  href={category.href}
                  className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl hover:bg-primary-50 transition-colors group"
                >
                  <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                    <category.icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-slate-900">{category.title}</h3>
                    <p className="text-sm text-slate-500">{category.description}</p>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Sections */}
      <section className="py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {Object.entries(faqData).map(([category, questions]) => {
            const filteredQuestions = questions.filter(q => filterFAQs(q.question));
            if (filteredQuestions.length === 0) return null;

            const categoryInfo = categories.find(c => c.href === `#${category}`);
            
            return (
              <div key={category} id={category} className="scroll-mt-32">
                <div className="flex items-center gap-3 mb-6">
                  {categoryInfo && (
                    <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
                      <categoryInfo.icon className="w-5 h-5 text-primary-600" />
                    </div>
                  )}
                  <h2 className="text-xl font-bold text-slate-900">
                    {categoryInfo?.title || category}
                  </h2>
                </div>
                <div className="bg-white rounded-2xl shadow-sm divide-y divide-slate-100">
                  {filteredQuestions.map((item, index) => {
                    const questionKey = `${category}-${index}`;
                    const isExpanded = expandedQuestions[questionKey];
                    
                    return (
                      <div key={index} className="p-4">
                        <button
                          onClick={() => toggleQuestion(questionKey)}
                          className="w-full flex items-center justify-between text-left"
                        >
                          <span className="font-medium text-slate-900 pr-4">{item.question}</span>
                          <ChevronRight
                            className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform ${
                              isExpanded ? 'rotate-90' : ''
                            }`}
                          />
                        </button>
                        {isExpanded && (
                          <div className="mt-3 text-slate-600 leading-relaxed">
                            {item.answer}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-bold text-slate-900 mb-6 text-center">快速入口</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: BookOpen, label: '法律知识库', href: '/knowledge' },
              { icon: Users, label: '找律师', href: '/lawyer' },
              { icon: FileText, label: '文书生成', href: '/document' },
              { icon: Scale, label: '合同审查', href: '/contracts' },
            ].map((item, index) => (
              <Link
                key={index}
                to={item.href}
                className="flex flex-col items-center gap-3 p-6 bg-slate-50 rounded-xl hover:bg-primary-50 transition-colors group"
              >
                <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                  <item.icon className="w-6 h-6 text-primary-600" />
                </div>
                <span className="font-medium text-slate-900">{item.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 text-white">
            <h2 className="text-xl font-bold mb-2">还没找到答案？</h2>
            <p className="text-slate-300 mb-6">联系我们的客服团队，我们随时为您提供帮助</p>
            <div className="grid sm:grid-cols-3 gap-4">
              {contactOptions.map((option, index) => (
                <div
                  key={index}
                  className="bg-white/10 rounded-xl p-4 backdrop-blur-sm"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <option.icon className="w-5 h-5 text-primary-400" />
                    <span className="font-medium">{option.title}</span>
                  </div>
                  {option.action.startsWith('/') ? (
                    <Link
                      to={option.action}
                      className="text-primary-400 hover:text-primary-300 font-medium"
                    >
                      {option.content}
                    </Link>
                  ) : (
                    <a
                      href={option.action}
                      className="text-primary-400 hover:text-primary-300 font-medium"
                    >
                      {option.content}
                    </a>
                  )}
                  <p className="text-sm text-slate-400 mt-1">{option.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Related Links */}
      <section className="py-12 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-bold text-slate-900 mb-6 text-center">相关链接</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { label: '用户协议', href: '/terms' },
              { label: '隐私政策', href: '/privacy' },
              { label: 'AI免责声明', href: '/ai-disclaimer' },
            ].map((item, index) => (
              <Link
                key={index}
                to={item.href}
                className="flex items-center justify-between p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors group"
              >
                <span className="font-medium text-slate-900">{item.label}</span>
                <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-primary-600 transition-colors" />
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}