# 贡献指南

感谢您考虑为百姓法律助手项目贡献代码！

## 开发规范

### 代码风格

#### Python (后端)
- 遵循 PEP 8 规范
- 使用类型注解
- 中文注释关键逻辑
- 函数长度不超过 100 行

#### TypeScript/React (前端)
- 遵循 ESLint 配置
- 使用 TypeScript 严格模式
- 组件使用函数式写法
- 合理拆分组件

### 提交规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例**：
```
feat(user): 添加手机号登录功能

fix(payment): 修复支付回调重复处理问题
```

## 开发流程

### 1. Fork 项目

```bash
# 访问 https://github.com/your-username/baixing-assistant
# 点击 Fork 按钮
```

### 2. 克隆代码

```bash
git clone https://github.com/YOUR_USERNAME/baixing-assistant.git
cd baixing-assistant
```

### 3. 创建分支

```bash
# 基于主分支创建功能分支
git checkout -b feature/your-feature-name
```

### 4. 开发与测试

```bash
# 后端开发
cd backend
py -m pytest tests/your_test.py -v

# 前端开发
cd frontend
npm run test:unit
```

### 5. 提交代码

```bash
git add .
git commit -m "feat(scope): description"
git push origin feature/your-feature-name
```

### 6. 创建 PR

在 GitHub 上创建 Pull Request，描述您的改动。

## 测试要求

### 后端测试
- 新增功能需配套单元测试
- 测试覆盖率不低于 62%
- 运行命令：`py -m pytest --cov=app`

### 前端测试
- 关键组件需编写测试
- E2E 测试覆盖核心流程
- 运行命令：`npm run test:unit`

## 代码审查

- PR 至少需要 1 人审查
- 所有 CI 检查通过
- 解决所有评论后再合并

## 行为准则

- 尊重他人意见
- 友好沟通
- 积极反馈