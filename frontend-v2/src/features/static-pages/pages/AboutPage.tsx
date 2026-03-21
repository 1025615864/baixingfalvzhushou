/**
 * 关于我们页面
 * 百姓助手法律服务平台介绍
 */

import { Link } from 'react-router-dom';
import {
  Scale,
  Shield,
  Users,
  Award,
  Target,
  Heart,
  Lightbulb,
  CheckCircle,
} from 'lucide-react';

const stats = [
  { label: '注册用户', value: '100万+' },
  { label: '合作律师', value: '5000+' },
  { label: '服务案例', value: '50万+' },
  { label: '覆盖城市', value: '300+' },
];

const values = [
  {
    icon: Shield,
    title: '专业可信',
    description: '严格审核律师资质，确保服务质量，让每一位用户都能获得专业的法律帮助',
  },
  {
    icon: Heart,
    title: '用户至上',
    description: '以用户需求为中心，提供便捷、高效、贴心的法律服务体验',
  },
  {
    icon: Lightbulb,
    title: '科技赋能',
    description: '运用人工智能技术，让法律服务更智能、更高效、更普惠',
  },
  {
    icon: Users,
    title: '开放共享',
    description: '构建开放的法律服务生态，连接律师、用户与法律资源',
  },
];

const milestones = [
  { year: '2021', event: '百姓助手正式上线，开启智能法律服务新篇章' },
  { year: '2022', event: '用户突破50万，获得A轮融资' },
  { year: '2023', event: '推出AI智能咨询系统，服务能力提升10倍' },
  { year: '2024', event: '用户突破100万，覆盖全国300+城市' },
  { year: '2025', event: '获得国家高新技术企业认证，入选法律服务创新案例' },
];

const team = [
  {
    name: '张明',
    role: '创始人兼CEO',
    description: '前知名律所合伙人，15年法律行业经验',
  },
  {
    name: '李华',
    role: '技术VP',
    description: '前互联网大厂技术专家，AI领域资深研究者',
  },
  {
    name: '王芳',
    role: '首席法务官',
    description: '法学博士，专注互联网法律研究',
  },
];

export function AboutPage(): JSX.Element {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-50" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full text-sm font-medium mb-6 backdrop-blur-sm">
              <Scale className="w-4 h-4" />
              <span>专业法律服务平台</span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              关于<span className="text-primary-200">百姓助手</span>
            </h1>
            <p className="text-xl md:text-2xl text-primary-100 max-w-3xl mx-auto leading-relaxed">
              致力于让每个人都能获得专业、便捷、可信赖的法律服务
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative -mt-10 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-primary-600 mb-2">
                    {stat.value}
                  </div>
                  <div className="text-slate-600">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-slate-900 mb-6">我们的使命</h2>
              <p className="text-lg text-slate-600 leading-relaxed mb-6">
                百姓助手成立于2021年，是一家专注于法律科技的互联网公司。我们相信，每个人都应该能够便捷地获取专业的法律服务，
                无论其经济状况或社会地位如何。
              </p>
              <p className="text-lg text-slate-600 leading-relaxed mb-6">
                通过人工智能技术与专业律师团队的结合，我们为用户提供智能法律咨询、律师匹配、合同审查、文书生成等全方位的法律服务，
                让法律服务不再高不可攀。
              </p>
              <div className="flex items-center gap-4">
                <Target className="w-6 h-6 text-primary-600" />
                <span className="text-slate-700 font-medium">让法律服务触手可及</span>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square bg-gradient-to-br from-primary-100 to-primary-200 rounded-3xl flex items-center justify-center">
                <Scale className="w-32 h-32 text-primary-600" />
              </div>
              <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-primary-600 rounded-2xl flex items-center justify-center">
                <Award className="w-12 h-12 text-white" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">核心价值观</h2>
            <p className="text-lg text-slate-600">我们坚持的理念，引领我们不断前行</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value, index) => (
              <div
                key={index}
                className="p-6 bg-slate-50 rounded-2xl hover:bg-primary-50 transition-colors group"
              >
                <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-primary-200 transition-colors">
                  <value.icon className="w-7 h-7 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">{value.title}</h3>
                <p className="text-slate-600">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">发展历程</h2>
            <p className="text-lg text-slate-600">一路走来的重要里程碑</p>
          </div>
          <div className="relative">
            <div className="absolute left-1/2 transform -translate-x-1/2 h-full w-0.5 bg-primary-200" />
            <div className="space-y-12">
              {milestones.map((milestone, index) => (
                <div
                  key={index}
                  className={`relative flex items-center ${
                    index % 2 === 0 ? 'flex-row' : 'flex-row-reverse'
                  }`}
                >
                  <div className={`w-1/2 ${index % 2 === 0 ? 'pr-12 text-right' : 'pl-12 text-left'}`}>
                    <div className="bg-white p-6 rounded-xl shadow-md inline-block">
                      <div className="text-primary-600 font-bold text-lg mb-1">{milestone.year}</div>
                      <div className="text-slate-600">{milestone.event}</div>
                    </div>
                  </div>
                  <div className="absolute left-1/2 transform -translate-x-1/2 w-4 h-4 bg-primary-600 rounded-full border-4 border-white shadow" />
                  <div className="w-1/2" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">核心团队</h2>
            <p className="text-lg text-slate-600">专业的团队，为您保驾护航</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {team.map((member, index) => (
              <div
                key={index}
                className="text-center p-8 bg-slate-50 rounded-2xl hover:shadow-lg transition-shadow"
              >
                <div className="w-24 h-24 bg-primary-100 rounded-full mx-auto mb-6 flex items-center justify-center">
                  <span className="text-3xl font-bold text-primary-600">
                    {member.name.charAt(0)}
                  </span>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-1">{member.name}</h3>
                <div className="text-primary-600 font-medium mb-3">{member.role}</div>
                <p className="text-slate-600">{member.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">我们的服务</h2>
            <p className="text-lg text-slate-600">全方位的法律服务解决方案</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { title: 'AI智能咨询', desc: '24小时在线，即时解答您的法律问题' },
              { title: '专业律师服务', desc: '严选5000+专业律师，一对一服务' },
              { title: '合同审查', desc: '专业合同审查，规避法律风险' },
              { title: '文书生成', desc: '智能生成法律文书，省时省力' },
              { title: '法律知识库', desc: '海量法律知识，自助学习' },
              { title: '法律资讯', desc: '最新法律动态，实时更新' },
            ].map((service, index) => (
              <div
                key={index}
                className="flex items-start gap-4 p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow"
              >
                <CheckCircle className="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-slate-900 mb-1">{service.title}</h3>
                  <p className="text-slate-600 text-sm">{service.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-primary-600 to-primary-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-6">开始您的法律服务之旅</h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            无论您遇到什么法律问题，百姓助手都将为您提供专业的解决方案
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/chat"
              className="inline-flex items-center justify-center px-8 py-3 bg-white text-primary-600 font-semibold rounded-xl hover:bg-primary-50 transition-colors"
            >
              立即咨询
            </Link>
            <Link
              to="/contact"
              className="inline-flex items-center justify-center px-8 py-3 bg-primary-500 text-white font-semibold rounded-xl hover:bg-primary-400 transition-colors"
            >
              联系我们
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}