# 股票智能筛选系统

一个基于 Python + Flask + Vue3 + Element Plus 的股票智能筛选系统，支持 AI 驱动的策略生成和数据分析。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Vue3)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 仪表盘   │ │股票管理 │ │策略管理 │ │ AI助手   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 层 (Flask)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 股票API  │ │策略API   │ │筛选API   │ │ AI API   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      服务层                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │数据获取  │ │策略执行  │ │AI分析    │ │数据存储  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ SQLite   │ │通达信    │ │LLM API   │                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 功能特性

### 核心功能
- **股票数据管理**: 支持 A 股数据导入、查询、更新
- **策略管理**: 可视化策略配置，支持多条件组合
- **智能筛选**: 实时执行筛选策略，获取符合条件的股票
- **AI 助手**: 自然语言生成策略，智能分析结果

### AI 功能
- **策略生成**: 用自然语言描述需求，AI 自动生成筛选条件
- **结果分析**: AI 分析筛选结果，提供投资建议
- **异常检测**: 自动识别数据异常和模式
- **策略优化**: 基于历史数据给出策略改进建议

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+

### 后端部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd tdx

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python start_server.py
# 或使用 Flask 命令
flask --app app:app run --host=0.0.0.0 --port=5000
```

### 前端部署

```bash
# 1. 进入前端目录
cd web-admin

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 生产构建
npm run build
```

### 配置 AI 功能

```bash
# 设置环境变量
export ANTHROPIC_API_KEY="your-api-key"
export OPENAI_API_KEY="your-api-key"

# 或使用 .env 文件
cp .env.example .env
# 编辑 .env 文件填入 API Key
```

## API 文档

### 基础信息
- **Base URL**: `http://localhost:5000/api`
- **文档地址**: `http://localhost:5000/docs`

### 主要接口

#### 股票管理
```
GET    /api/stocks              # 获取股票列表
GET    /api/stocks/:code        # 获取股票详情
POST   /api/stocks              # 创建股票
PUT    /api/stocks/:code        # 更新股票
DELETE /api/stocks/:code        # 删除股票
```

#### 策略管理
```
GET    /api/strategies              # 获取策略列表
GET    /api/strategies/:id           # 获取策略详情
POST   /api/strategies               # 创建策略
POST   /api/strategies/generate     # AI生成策略
PUT    /api/strategies/:id          # 更新策略
DELETE /api/strategies/:id          # 删除策略
```

#### 筛选执行
```
POST   /api/screening/execute              # 执行筛选
GET    /api/screening-results             # 获取结果列表
GET    /api/screening-results/:id         # 获取结果详情
POST   /api/screening-results/:id/analyze  # AI分析结果
```

## 项目结构

```
tdx/
├── app.py                    # Flask 应用入口
├── start_server.py           # 服务启动脚本
├── api.py                    # API 路由
├── config.py                 # 配置管理
├── database.py               # 数据库操作
├── models.py                 # 数据模型
├── schemas.py                # 数据验证
├── middlewares.py            # 中间件
├── strategy.py             # 策略模块
├── data_fetcher.py         # 数据获取
├── ai_analyzer.py          # AI 分析
├── main.py                 # CLI 入口
├── requirements.txt        # Python 依赖
├── tdxPj.py               # 原始脚本
├── stock_list.txt          # 股票列表
└── web-admin/              # 前端项目
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/
        ├── store/
        ├── api/
        ├── components/
        └── views/
```

## 技术栈

### 后端
- **Flask**: Web 框架
- **SQLAlchemy**: ORM
- **Pydantic**: 数据验证
- **mootdx**: 通达信数据接口

### 前端
- **Vue 3**: 前端框架
- **Element Plus**: UI 组件库
- **Pinia**: 状态管理
- **ECharts**: 图表库
- **Axios**: HTTP 客户端

### AI
- **Anthropic Claude**: LLM 模型
- **OpenAI GPT**: 备选 LLM

## 开发指南

### 添加新策略条件

```python
# 在 config.py 中添加条件定义
FilterCondition(
    name="市盈率",
    field="pe_ratio",
    operator="<",
    value=20
)
```

### 自定义 AI 提示词

```python
# 在 ai_analyzer.py 中修改提示词
prompt = f"""
你的自定义提示词...
描述: {description}
"""
```

### 添加新的 API 端点

```python
# 在 api.py 中添加路由
@api_bp.route('/custom', methods=['POST'])
def custom_endpoint():
    data = request.get_json()
    # 处理逻辑
    return success_response(result)
```

## 测试

```bash
# 运行测试
pytest tests/

# 生成覆盖率报告
pytest --cov=tdx tests/
```

## 部署

### Docker 部署

```bash
# 构建镜像
docker build -t tdx-screener .

# 运行容器
docker run -d \
  -p 5000:5000 \
  -p 3000:3000 \
  -e ANTHROPIC_API_KEY=xxx \
  tdx-screener
```

### 生产环境配置

```bash
# 设置环境变量
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=sqlite:///production.db

# 使用 Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 项目主页: https://github.com/yourusername/tdx-screener
- 问题反馈: https://github.com/yourusername/tdx-screener/issues
