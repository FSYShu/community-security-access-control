# 社区安防门禁系统

融合人脸识别通行、危险区域入侵检测、实时视频异常行为识别与统一告警中心的智能化门禁安防系统。

## 技术栈

- **前端（物业后台端）**: Vue 2 + Vant 2 + Vuex + Vue Router
- **前端（门禁端）**: Vue 2 + Vant 2（独立应用，浏览器调用摄像头）
- **后端**: Python + Flask
- **数据库**: SQLite（WAL 模式）
- **流媒体**: Nginx-RTMP
- **人脸识别**: dlib
- **CI/CD**: Jenkins
- **部署**: Docker Compose

## 项目结构

```
├── backend/                    # Flask 后端
│   ├── app/
│   │   ├── __init__.py         # 应用工厂
│   │   ├── auth/               # 认证模块
│   │   ├── face/               # 人脸管理模块
│   │   ├── alarm/              # 告警中心模块
│   │   ├── danger_zone/        # 禁区入侵检测模块
│   │   ├── video_monitor/      # 视频监控模块（RTMP拉流+MJPEG转发）
│   │   ├── gate/               # 门禁终端管理模块
│   │   ├── report/             # 安防日报模块
│   │   ├── property/           # 物业后台模块
│   │   └── models/             # 数据模型
│   ├── config/                 # 多环境配置
│   ├── tests/                  # 单元测试
│   ├── utils/                  # 工具模块
│   └── requirements.txt        # Python 依赖
├── src/                        # 物业后台端 Vue 应用
│   ├── api/                    # 接口模块
│   ├── views/                  # 页面组件
│   ├── router/                 # 路由配置
│   ├── store/                  # Vuex 状态管理
│   └── utils/                  # 工具函数
├── frontend-gate/              # 门禁端 Vue 应用（独立）
├── nginx-rtmp/                 # Nginx-RTMP 配置
├── docker-compose.yml          # Docker 编排
├── Dockerfile.backend          # 后端 Docker 镜像
├── Dockerfile.frontend         # 前端 Docker 镜像
├── Jenkinsfile                 # Jenkins CI/CD Pipeline
└── .env                        # 环境变量配置
```

## 核心功能

| 模块 | 说明 |
|------|------|
| 人脸识别通行 | 业主/访客/黑名单人脸识别，dlib 128维编码比对，层级权限校验 |
| 危险区域入侵检测 | 禁区入侵、安全距离预警、滞留告警升级 |
| 实时视频异常检测 | 陌生人逗留、破坏设备、明火、烟雾检测，分级告警推送 |
| 告警中心管理 | 四类告警分类筛选、处置标记、视频回放、Excel 导出 |
| 物业后台管理 | 人脸信息管理、门禁终端层级管理、权限配置、安防日报 |
| 门禁端 Web 应用 | 浏览器摄像头人脸通行、访客临时授权申请、响应式适配 |
| 视频推流管理 | Nginx-RTMP 推流/拉流、鉴权、告警短视频录制与回放 |

## 快速开始

### 环境要求

- Node.js >= 12
- Python >= 3.7
- Nginx + nginx-rtmp-module（推流服务器）

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

### 前端启动（物业后台端）

```bash
npm install
npm run dev
```

### 前端启动（门禁端）

```bash
cd frontend-gate
npm install
npm run dev
```

### 环境变量

在 `.env` 文件中配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `RTMP_SERVER_HOST` | Nginx-RTMP 服务器地址 | 20.214.147.223 |
| `RTMP_SERVER_PORT` | RTMP 端口 | 9090 |
| `SECRET_KEY` | Flask 密钥 | - |
| `JWT_SECRET_KEY` | JWT 密钥 | - |

### Docker 部署

```bash
docker-compose up -d
```

## 用户角色

- **业主**: 人脸识别通行、访客授权审批、人脸信息管理
- **物业管理员**: 统一管理人脸/门禁/权限/告警、安防日报
- **安保人员**: 实时告警查看与处置、视频监控

## 运行测试

```bash
# 后端单元测试
cd backend
python -m pytest tests/ -v

# 前端单元测试
npm run unit

# 前端构建
npm run build
```
