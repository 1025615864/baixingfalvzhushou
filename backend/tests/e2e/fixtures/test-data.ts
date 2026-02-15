/**
 * 测试数据fixtures
 * 
 * 提供E2E测试所需的测试数据
 */

export interface TestUser {
  email: string;
  password: string;
  name: string;
  phone?: string;
}

export interface TestConsultation {
  title: string;
  description: string;
  category: string;
  tags: string[];
}

export interface TestChatMessage {
  content: string;
  type: 'user' | 'assistant' | 'system';
}

export const testUsers: Record<string, TestUser> = {
  defaultUser: {
    email: 'test@example.com',
    password: 'password123',
    name: '测试用户',
    phone: '13800138000',
  },
  vipUser: {
    email: 'vip@example.com',
    password: 'password123',
    name: 'VIP用户',
    phone: '13800138001',
  },
  lawyerUser: {
    email: 'lawyer@example.com',
    password: 'password123',
    name: '律师用户',
    phone: '13800138002',
  },
  adminUser: {
    email: 'admin@example.com',
    password: 'admin123',
    name: '管理员',
    phone: '13800138003',
  },
};

export const testConsultations: TestConsultation[] = [
  {
    title: '劳动合同纠纷咨询',
    description: '我想咨询一下关于劳动合同解除的问题',
    category: 'labor',
    tags: ['劳动合同', '解除', '赔偿'],
  },
  {
    title: '房屋租赁合同问题',
    description: '房东拒绝退还押金怎么办',
    category: 'property',
    tags: ['租赁', '押金', '违约'],
  },
  {
    title: '离婚财产分割',
    description: '请教一下离婚时的财产分割问题',
    category: 'family',
    tags: ['离婚', '财产', '分割'],
  },
];

export const testChatMessages: TestChatMessage[] = [
  {
    content: '你好，我想咨询劳动合同问题',
    type: 'user',
  },
  {
    content: '您好！请问您具体遇到什么劳动合同问题？比如是关于合同签订、解除还是其他方面？',
    type: 'assistant',
  },
  {
    content: '公司无故解除劳动合同，我想了解赔偿标准',
    type: 'user',
  }
];

export const testDocuments = {
  contractTemplate: `
劳动合同

甲方：[公司名称]
乙方：[员工姓名]

一、劳动合同期限
本合同为固定期限劳动合同，自____年____月____日起至____年____月____日止。

二、工作内容和工作地点
乙方同意根据甲方工作需要，担任____岗位工作。
乙方的工作地点为____。

三、工作时间和休息休假
甲方执行标准工时制度。
乙方依法享受国家规定的各类假期。

四、劳动报酬
乙方月工资为____元。
甲方每月____日发放工资。
  `,
  leaseAgreement: `
房屋租赁合同

出租方（甲方）：[姓名]
承租方（乙方）：[姓名]

一、房屋基本情况
甲方将其位于____的房屋出租给乙方使用。
房屋建筑面积为____平方米。

二、租赁期限
租赁期限为____年，自____年____月____日起至____年____月____日止。

三、租金及支付方式
月租金为____元。
租金支付方式为____。
押金为____元。
  `
};

export const mockAPIResponses = {
  loginSuccess: {
    success: true,
    data: {
      token: 'mock-token-123456',
      user: testUsers.defaultUser,
    },
  },
  loginError: {
    success: false,
    error: '用户名或密码错误',
  },
  getUserInfo: {
    success: true,
    data: testUsers.defaultUser,
  },
  chatResponse: {
    success: true,
    data: {
      message: '根据您的问题，我建议您...',
      timestamp: Date.now(),
    },
  },
  consultationList: {
    success: true,
    data: {
      total: 10,
      items: testConsultations,
    },
  },
};