/**
 * 用户协议页面
 * 百姓助手法律服务平台用户服务协议
 */

import { Link } from 'react-router-dom';
import { Scale, Calendar, ChevronRight } from 'lucide-react';

const sections = [
  { id: 'intro', title: '一、总则' },
  { id: 'account', title: '二、账户注册与使用' },
  { id: 'service', title: '三、服务内容' },
  { id: 'rights', title: '四、用户权利与义务' },
  { id: 'payment', title: '五、付费服务' },
  { id: 'ai', title: '六、AI服务特别说明' },
  { id: 'privacy', title: '七、隐私保护' },
  { id: 'intellectual', title: '八、知识产权' },
  { id: 'liability', title: '九、责任限制' },
  { id: 'termination', title: '十、协议终止' },
  { id: 'dispute', title: '十一、争议解决' },
  { id: 'misc', title: '十二、其他条款' },
];

export function TermsPage(): JSX.Element {
  const lastUpdateDate = '2025年1月1日';

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-slate-800 to-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full text-sm font-medium mb-6">
              <Scale className="w-4 h-4" />
              <span>法律条款</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4">用户服务协议</h1>
            <p className="text-slate-300 flex items-center justify-center gap-2">
              <Calendar className="w-4 h-4" />
              最后更新日期：{lastUpdateDate}
            </p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <section className="bg-white border-b border-slate-200 sticky top-16 z-20">
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
              <p className="text-slate-600 mb-8">
                欢迎您使用百姓助手平台！为使用百姓助手平台服务（以下简称「本服务」），您应当阅读并遵守《百姓助手用户服务协议》（以下简称「本协议」）。
                请您务必审慎阅读、充分理解各条款内容，特别是免除或限制责任的相应条款。
                <strong>除非您已阅读并接受本协议所有条款，否则您无权使用本服务。</strong>
              </p>

              <h2 id="intro" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">1</span>
                总则
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>1.1</strong> 本协议是您与百姓助手平台（以下简称「我们」或「平台」）之间关于使用本服务所订立的协议。</p>
                <p><strong>1.2</strong> 本服务由百姓助手运营提供。「用户」指通过本服务注册账户并使用本服务的个人或组织。</p>
                <p><strong>1.3</strong> 您通过网络页面点击「同意」按钮或实际使用本服务，即表示您已充分阅读、理解并接受本协议的全部内容。</p>
                <p><strong>1.4</strong> 我们有权在必要时修改本协议条款。您可以在相关服务页面查阅最新版本的协议条款。</p>
              </div>

              <h2 id="account" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">2</span>
                账户注册与使用
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>2.1 账户注册</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>您需要注册一个百姓助手账户才能使用本服务的部分功能。</li>
                  <li>您承诺在注册时提供的信息真实、准确、完整，并及时更新。</li>
                  <li>您应当年满18周岁或具备相应的民事行为能力。</li>
                  <li>每个用户只能注册一个账户，不得重复注册。</li>
                </ul>
                <p><strong>2.2 账户安全</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>您有责任妥善保管账户信息和密码。</li>
                  <li>因您保管不当可能造成的损失，由您自行承担。</li>
                  <li>如发现账户被盗用或存在安全漏洞，应立即通知我们。</li>
                </ul>
                <p><strong>2.3 账户使用规范</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>不得将账户转让、出借给他人使用。</li>
                  <li>不得使用账户从事违法违规活动。</li>
                  <li>不得利用账户侵犯他人合法权益。</li>
                </ul>
              </div>

              <h2 id="service" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">3</span>
                服务内容
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>3.1</strong> 本平台提供以下服务：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>AI智能法律咨询服务</li>
                  <li>律师在线咨询与匹配服务</li>
                  <li>法律文书生成服务</li>
                  <li>合同审查服务</li>
                  <li>法律知识库查询服务</li>
                  <li>法律资讯服务</li>
                  <li>其他相关法律服务</li>
                </ul>
                <p><strong>3.2</strong> 我们保留随时修改、中断或终止部分或全部服务的权利。</p>
                <p><strong>3.3</strong> 服务的具体内容以平台实际提供的为准。</p>
              </div>

              <h2 id="rights" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">4</span>
                用户权利与义务
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>4.1 用户权利</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>依法使用本平台提供的各项服务</li>
                  <li>对账户信息进行查询、更正和删除</li>
                  <li>对本平台服务提出意见和建议</li>
                  <li>依法享有的其他权利</li>
                </ul>
                <p><strong>4.2 用户义务</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>遵守国家法律法规及本协议各项规定</li>
                  <li>不得发布违法、虚假、侵权或不当内容</li>
                  <li>不得干扰或破坏平台的正常运营</li>
                  <li>不得利用平台从事欺诈或其他违法活动</li>
                  <li>对使用账户进行的所有活动负责</li>
                </ul>
              </div>

              <h2 id="payment" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">5</span>
                付费服务
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>5.1</strong> 部分服务需要付费使用，具体收费标准以平台公示为准。</p>
                <p><strong>5.2</strong> 您在进行付费前应仔细核对订单信息，一旦付款成功，除法律规定或平台另有规定外，不予退款。</p>
                <p><strong>5.3</strong> 会员服务一经开通，在有效期内不支持退款。</p>
                <p><strong>5.4</strong> 如有优惠活动，以活动规则为准。</p>
              </div>

              <h2 id="ai" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">6</span>
                AI服务特别说明
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>6.1 咨询性质</strong></p>
                <p>本平台提供的AI智能法律咨询服务基于人工智能技术，仅供参考，<strong>不构成正式的法律意见或建议</strong>。</p>
                <p><strong>6.2 限制说明</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>AI咨询结果可能存在不准确或不完整的情况</li>
                  <li>AI无法替代专业律师的法律服务</li>
                  <li>对于复杂或重大法律问题，建议咨询专业律师</li>
                </ul>
                <p><strong>6.3 责任免除</strong></p>
                <p>因依赖AI咨询服务而产生的任何损失，平台不承担赔偿责任。但我们会持续优化AI服务，提高咨询质量。</p>
              </div>

              <h2 id="privacy" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">7</span>
                隐私保护
              </h2>
              <div className="space-y-4 text-slate-600">
                <p>我们重视用户隐私保护。关于用户个人信息的收集、使用、存储等事宜，请参阅我们的<Link to="/privacy" className="text-primary-600 hover:text-primary-700">《隐私政策》</Link>。</p>
              </div>

              <h2 id="intellectual" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">8</span>
                知识产权
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>8.1</strong> 本平台的Logo、「百姓助手」名称、软件、技术、程序、网页设计等知识产权均归平台所有。</p>
                <p><strong>8.2</strong> 未经书面授权，任何人不得擅自使用上述知识产权。</p>
                <p><strong>8.3</strong> 用户在平台发布的内容，用户保证拥有合法权利，不侵犯他人知识产权。</p>
              </div>

              <h2 id="liability" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">9</span>
                责任限制
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>9.1</strong> 在法律允许的最大范围内，以下情况我们不承担责任：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>不可抗力或第三方原因导致的服务中断</li>
                  <li>因用户原因（如密码泄露）造成的损失</li>
                  <li>用户使用本服务产生的间接损失</li>
                  <li>因AI咨询结果不准确导致的损失</li>
                </ul>
                <p><strong>9.2</strong> 在任何情况下，我们的赔偿责任不超过您就相关服务实际支付的费用。</p>
              </div>

              <h2 id="termination" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">10</span>
                协议终止
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>10.1 用户终止</strong></p>
                <p>您有权随时注销账户并终止本协议。账户注销后，您将无法使用本服务。</p>
                <p><strong>10.2 平台终止</strong></p>
                <p>如您违反本协议规定，我们有权暂停或终止向您提供服务，并保留追究法律责任的权利。</p>
              </div>

              <h2 id="dispute" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">11</span>
                争议解决
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>11.1</strong> 本协议的订立、执行、解释及争议解决均适用中华人民共和国法律。</p>
                <p><strong>11.2</strong> 因本协议或本服务引起的任何争议，双方应首先友好协商解决。</p>
                <p><strong>11.3</strong> 如协商不成，任何一方均可向平台所在地人民法院提起诉讼。</p>
              </div>

              <h2 id="misc" className="text-xl font-bold text-slate-900 mt-8 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center text-sm">12</span>
                其他条款
              </h2>
              <div className="space-y-4 text-slate-600">
                <p><strong>12.1</strong> 本协议中的任何条款如被认定无效或不可执行，不影响其他条款的效力。</p>
                <p><strong>12.2</strong> 我们未行使或延迟行使本协议项下的任何权利，不构成对该权利的放弃。</p>
                <p><strong>12.3</strong> 本协议标题仅供参考，不影响条款的含义或解释。</p>
                <p><strong>12.4</strong> 如有任何问题，请联系我们：</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>客服热线：400-888-8888</li>
                  <li>客服邮箱：service@baixing.com</li>
                  <li>公司地址：北京市朝阳区建国路88号</li>
                </ul>
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
              to="/privacy"
              className="flex items-center justify-between p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow group"
            >
              <div>
                <h3 className="font-semibold text-slate-900">隐私政策</h3>
                <p className="text-sm text-slate-500">了解我们如何保护您的个人信息</p>
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