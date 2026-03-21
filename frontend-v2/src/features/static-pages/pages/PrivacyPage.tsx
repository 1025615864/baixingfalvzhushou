/**
 * 隐私政策页面
 * 百姓助手法律服务平台隐私保护政策
 */

import { Link } from 'react-router-dom';
import { Shield, Calendar, ChevronRight, Lock, Eye, Database, UserCheck } from 'lucide-react';

const sections = [
  { id: 'intro', title: '一、引言' },
  { id: 'collect', title: '二、信息收集' },
  { id: 'use', title: '三、信息使用' },
  { id: 'share', title: '四、信息共享' },
  { id: 'security', title: '五、信息安全' },
  { id: 'rights', title: '六、您的权利' },
  { id: 'cookies', title: '七、Cookie政策' },
  { id: 'children', title: '八、儿童隐私' },
  { id: 'update', title: '九、政策更新' },
  { id: 'contact', title: '十、联系我们' },
];

const infoTypes = [
  {
    icon: UserCheck,
    title: '账户信息',
    description: '注册时提供的姓名、手机号、邮箱等基本信息',
  },
  {
    icon: Database,
    title: '使用记录',
    description: '您使用服务时产生的咨询记录、浏览记录等',
  },
  {
    icon: Lock,
    title: '身份验证',
    description: '为保障账户安全而收集的身份验证信息',
  },
  {
    icon: Eye,
    title: '设备信息',
    description: '设备型号、操作系统、浏览器类型等技术信息',
  },
];

export function PrivacyPage(): JSX.Element {
  const lastUpdateDate = '2025年1月1日';

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full text-sm font-medium mb-6">
              <Shield className="w-4 h-4" />
              <span>隐私保护</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4">隐私政策</h1>
            <p className="text-primary-100 flex items-center justify-center gap-2">
              <Calendar className="w-4 h-4" />
              最后更新日期：{lastUpdateDate}
            </p>
          </div>
        </div>
      </section>

      {/* Key Points */}
      <section className="relative -mt-6 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 text-center">我们收集的信息类型</h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {infoTypes.map((item, index) => (
                <div key={index} className="text-center p-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                    <item.icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="font-medium text-slate-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-slate-500">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <section className="bg-white border-b border-slate-200 sticky top-16 z-20 mt-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4 overflow-x-auto">
            <div className="flex gap-4 text-sm whitespace-nowrap">
              {sections.map(section => (
                <a
                  key={section.id}
                  href={`#${section.id}`}
                  className="text-slate-600 hover:text-primary-600 transition-colors"
                >
                  {section.title}
                </a>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-sm p-8 md:p-12">
            <div className="prose prose-slate max-w-none">
              <h2 id="intro" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">1</span>
                引言
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>
                  百姓助手（以下简称「我们」）深知个人信息对您的重要性，我们将按照法律法规要求，采取相应的安全保护措施，尽力保护您的个人信息安全可控。
                </p>
                <p>
                  本隐私政策旨在向您说明我们如何收集、使用、存储、共享和保护您的个人信息，以及您享有的相关权利。
                </p>
                <p>
                  <strong>请您仔细阅读本隐私政策。如果您不同意本政策的任何内容，您应立即停止使用我们的服务。</strong>
                </p>
              </div>

              <h2 id="collect" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">2</span>
                信息收集
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>2.1 我们收集的信息</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>账户信息：</strong>注册时提供的姓名、手机号码、电子邮箱、密码等。</li>
                  <li><strong>身份信息：</strong>实名认证时提供的身份证号、人脸信息等（仅在您主动提供时收集）。</li>
                  <li><strong>使用信息：</strong>咨询记录、浏览记录、搜索记录、订单信息等。</li>
                  <li><strong>设备信息：</strong>设备型号、操作系统、唯一设备标识符、浏览器类型等。</li>
                  <li><strong>位置信息：</strong>在获得您授权后收集的大致地理位置信息。</li>
                  <li><strong>支付信息：</strong>支付方式、交易记录等（支付详情由第三方支付平台处理）。</li>
                </ul>
                <p><strong>2.2 信息收集方式</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>您主动提供的信息</li>
                  <li>您使用服务时自动收集的信息</li>
                  <li>第三方来源的信息（如第三方登录）</li>
                </ul>
                <p><strong>2.3 我们不会收集的信息</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>您的种族、宗教信仰、政治观点等敏感信息</li>
                  <li>您的基因、指纹、声纹等生物识别信息（除非您主动提供用于身份验证）</li>
                  <li>您的医疗健康信息（除非您主动提供用于相关服务）</li>
                </ul>
              </div>

              <h2 id="use" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">3</span>
                信息使用
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>我们收集的信息将用于以下目的：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>提供、维护和改进我们的服务</li>
                  <li>处理您的咨询请求和订单</li>
                  <li>向您发送服务通知和更新</li>
                  <li>个性化您的使用体验</li>
                  <li>保障服务安全和防范欺诈</li>
                  <li>遵守法律法规要求</li>
                  <li>经您同意的其他用途</li>
                </ul>
              </div>

              <h2 id="share" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">4</span>
                信息共享
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>4.1 我们不会向第三方出售您的个人信息。</strong></p>
                <p><strong>4.2 以下情况下我们可能会共享您的信息：</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>服务提供商：</strong>与帮助我们运营业务的合作伙伴共享（如支付、云服务、数据分析等）</li>
                  <li><strong>律师服务：</strong>当您使用律师咨询服务时，我们会向相关律师提供必要信息</li>
                  <li><strong>法律要求：</strong>根据法律法规、法律程序或政府要求</li>
                  <li><strong>保护权益：</strong>为保护我们、用户或公众的权利、财产或安全</li>
                  <li><strong>经您同意：</strong>获得您明确同意的其他共享情况</li>
                </ul>
                <p><strong>4.3 跨境传输</strong></p>
                <p>如需将您的个人信息传输至境外，我们将遵守相关法律法规，并采取必要的安全措施。</p>
              </div>

              <h2 id="security" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">5</span>
                信息安全
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>我们采取多种安全措施保护您的个人信息：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>数据加密存储和传输（SSL/TLS加密）</li>
                  <li>访问控制和权限管理</li>
                  <li>安全审计和监控</li>
                  <li>员工安全培训</li>
                  <li>应急响应机制</li>
                  <li>定期安全评估</li>
                </ul>
                <p>
                  <strong>数据保留：</strong>我们仅在实现本政策所述目的所需的期限内保留您的个人信息，或法律要求的期限内保留。
                </p>
              </div>

              <h2 id="rights" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">6</span>
                您的权利
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>您对您的个人信息享有以下权利：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>访问权：</strong>您有权访问我们持有的您的个人信息</li>
                  <li><strong>更正权：</strong>您有权要求更正不准确或不完整的个人信息</li>
                  <li><strong>删除权：</strong>在特定情况下，您有权要求删除您的个人信息</li>
                  <li><strong>限制处理权：</strong>在特定情况下，您有权要求限制处理您的个人信息</li>
                  <li><strong>数据携带权：</strong>您有权以结构化格式获取您的个人信息</li>
                  <li><strong>撤回同意权：</strong>您有权随时撤回之前给予的同意</li>
                  <li><strong>注销账户：</strong>您有权注销您的账户</li>
                </ul>
                <p>
                  如需行使上述权利，请通过本政策末尾的联系方式与我们联系。
                </p>
              </div>

              <h2 id="cookies" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">7</span>
                Cookie政策
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>我们使用Cookie和类似技术来：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>记住您的登录状态</li>
                  <li>记住您的偏好设置</li>
                  <li>分析您如何使用我们的服务</li>
                  <li>个性化您的内容和广告</li>
                </ul>
                <p>
                  您可以通过浏览器设置管理Cookie，但这可能影响您使用我们服务的某些功能。
                </p>
              </div>

              <h2 id="children" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">8</span>
                儿童隐私
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>
                  我们的服务面向18周岁及以上的用户。我们不会故意收集18周岁以下儿童的个人信息。
                  如果您发现您的孩子在未经您同意的情况下向我们提供了个人信息，请立即联系我们。
                </p>
              </div>

              <h2 id="update" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">9</span>
                政策更新
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>
                  我们可能会不时更新本隐私政策。更新后的政策将在本页面发布，并在页面顶部注明最后更新日期。
                </p>
                <p>
                  对于重大变更，我们会通过站内信、邮件或其他方式通知您。建议您定期查阅本政策。
                </p>
              </div>

              <h2 id="contact" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">10</span>
                联系我们
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>如果您对本隐私政策有任何疑问、意见或请求，请通过以下方式联系我们：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>客服热线：</strong>400-888-8888</li>
                  <li><strong>隐私邮箱：</strong>privacy@baixing.com</li>
                  <li><strong>公司地址：</strong>北京市朝阳区建国路88号</li>
                </ul>
                <p>
                  我们将在收到您的请求后15个工作日内予以答复。
                </p>
              </div>

              <div className="mt-12 pt-8 border-t border-slate-200">
                <p className="text-center text-slate-500">
                  百姓助手法律服务平台
                  <br />
                  {lastUpdateDate}
                </p>
              </div>
            </div>
          </div>

          {/* Related Links */}
          <div className="mt-8 grid md:grid-cols-2 gap-4">
            <Link
              to="/terms"
              className="flex items-center justify-between p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow group"
            >
              <div>
                <h3 className="font-semibold text-slate-900">用户协议</h3>
                <p className="text-sm text-slate-500">了解使用我们服务的条款和条件</p>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-primary-600 transition-colors" />
            </Link>
            <Link
              to="/ai-disclaimer"
              className="flex items-center justify-between p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow group"
            >
              <div>
                <h3 className="font-semibold text-slate-900">AI免责声明</h3>
                <p className="text-sm text-slate-500">了解AI服务的使用限制和风险提示</p>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-primary-600 transition-colors" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}