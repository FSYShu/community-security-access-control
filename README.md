# 社区安防门禁系统

融合人脸识别通行、危险区域入侵检测、实时视频异常行为识别与统一告警中心的智能化社区门禁安防系统。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端（物业后台） | Vue 2.7 + Element UI 2.15 + Vuex 3 + ECharts 5 + flv.js |
| 前端（门禁端） | Vue 2 + Vant 2（独立应用，浏览器调用摄像头） |
| 后端 | Python + Flask 3 + Flask-SQLAlchemy + Flask-JWT-Extended + Flask-CORS + Flask-Limiter |
| 数据库 | SQLite（WAL 模式） |
| 流媒体 | Nginx-RTMP + FFmpeg（推拉流中继） |
| 人脸识别 | dlib（68 点关键点 + ResNet 128 维编码） |
| 异常检测 | OpenCV DNN + MobileNet SSD（人员检测）+ HSV 色彩分析（烟火）+ 光流法（设备破坏） |
| AI 日报 | SiliconFlow API (Qwen2.5-7B-Instruct) + 本地规则引擎降级 |
| CI/CD | Jenkins |
| 部署 | Docker Compose + Gunicorn |

## 项目结构

```
├── backend/                    # Flask 后端
│   ├── app/
│   │   ├── __init__.py         # 应用工厂 + 后台任务启动
│   │   ├── auth/               # 认证模块（登录/注册/角色权限）
│   │   ├── face/               # 人脸管理（注册/识别/活体检测）
│   │   ├── alarm/              # 告警中心（分类筛选/处置/导出）
│   │   ├── danger_zone/        # 禁区入侵检测（距离估算/滞留告警）
│   │   ├── video_monitor/      # 视频监控（MJPEG/SSE/推拉流管理）
│   │   ├── gate/               # 门禁终端管理（层级/权限/心跳）
│   │   ├── report/             # 安防日报（AI 生成/规则降级）
│   │   ├── property/           # 物业后台（通行日志/批量导入）
│   │   ├── gate_level/         # 门禁层级管理（社区/单元/入户/禁区）
│   │   ├── stream/             # 推流通道管理（CRUD/录制/回放）
│   │   ├── visitor_auth/       # 访客授权（申请/审批/自动清理）
│   │   ├── audit/              # 审计日志
│   │   ├── dashboard/          # 安防总览
│   │   └── models/             # 数据模型（11 表）
│   ├── core/                   # AI/CV 核心引擎
│   │   ├── face_recognition.py # dlib 人脸识别（128 维编码/0.4 阈值）
│   │   ├── liveness.py         # 活体检测（主动挑战 + 被动分析）
│   │   ├── danger_zone_detector.py  # 禁区入侵检测（双重策略）
│   │   ├── tailgating_detector.py    # 尾随检测（MobileNet SSD + 质心跟踪）
│   │   ├── fire_smoke_detector.py    # 烟火检测（HSV + 运动区域）
│   │   ├── device_tamper.py          # 设备防破坏（遮挡/模糊/移动/拍打）
│   │   ├── alarm_dedup.py            # 告警去重（线程级写锁）
│   │   ├── rtmp_relay.py             # RTMP 推拉流中继（FFmpeg）
│   │   └── shared_frame_store.py     # 共享帧存储
│   ├── config/                 # 多环境配置
│   ├── tests/                  # 单元测试
│   └── requirements.txt        # Python 依赖
├── src/                        # 物业后台端 Vue 应用
│   ├── api/                    # 接口模块
│   ├── views/                  # 页面组件
│   ├── router/                 # 路由配置
│   ├── store/                  # Vuex 状态管理
│   └── utils/                  # 工具函数
├── frontend-gate/              # 门禁端 Vue 应用（独立）
├── docker-compose.yml          # Docker 编排
├── Dockerfile.backend          # 后端 Docker 镜像
├── Dockerfile.frontend         # 前端 Docker 镜像
├── Jenkinsfile                 # Jenkins CI/CD Pipeline
└── .env                        # 环境变量配置
```

## 核心功能

### 人脸识别通行

- dlib 68 点关键点检测 + ResNet 128 维编码比对（阈值 0.4）
- 主动活体检测：随机动作挑战（眨眼/转头/张嘴），4 次尝试机会
- 被动活体检测：5 帧连续分析，区分照片欺骗与视频回放
- 层级权限校验：社区大门 → 单元门 → 入户门，危险区域必须二次验证

### 危险区域入侵检测

- 双重检测策略：优先人脸检测，无人脸时退而使用运动检测
- 基于标定的距离估算（近大远小原理）
- 安全距离预警 + 滞留告警升级（可配置停留时长）
- 30 秒告警冷却，防止重复告警

### 实时视频异常检测

- **尾随检测**：MobileNet SSD 人员检测 + CentroidTracker 质心跟踪 + 虚拟越线判定
- **烟火检测**：HSV 色彩空间火焰/烟雾识别 + 运动区域 + 形态学滤波 + 连续帧确认
- **设备防破坏**：遮挡/模糊/移动/拍打多状态分类 + 光流法运动反转检测 + 基线学习
- 分级告警推送 + 告警去重

### 告警中心管理

- 四类告警分类筛选（入侵/烟火/破坏/欺骗）
- 处置标记、视频回放、Excel 导出
- 线程级写锁保证告警去重一致性

### 门禁终端管理

- 层级嵌套：社区大门 → 单元门 → 入户门 → 危险防护区域
- 严格命名校验（方位+数字+门 / 栋单元 / 室号）
- 终端心跳监控 + 推流通道绑定
- 访客临时授权：申请 → 审批 → 通行后自动清理

### 安防日报

- AI 工作流：SiliconFlow API (Qwen2.5-7B-Instruct) 生成摘要与建议
- 降级机制：API 不可用时自动切换本地规则引擎
- AI 仅允许改写/简化已有建议，不得编造事件

### 视频推流管理

- 门禁端 JPEG 帧 → FFmpeg → RTMP 推流 → Nginx-RTMP
- RTMP 拉流 → FFmpeg → MJPEG/FLV 前端播放
- 引用计数共享拉流进程，SSE 检测端点复用共享帧
- 延迟监控 + FPS 统计

## 用户角色

| 角色 | 权限 |
|------|------|
| 业主 | 人脸识别通行、访客授权审批、人脸信息管理 |
| 物业管理员 | 统一管理人脸/门禁/权限/告警、安防日报、审计日志 |
| 安保人员 | 实时告警查看与处置、视频监控 |

## 快速开始

### 环境要求

- Node.js >= 12
- Python >= 3.7
- Nginx + nginx-rtmp-module（推流服务器）

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python start.py
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
| `RTMP_SERVER_HOST` | Nginx-RTMP 服务器地址 | - |
| `RTMP_SERVER_PORT` | RTMP 端口 | 9090 |
| `SECRET_KEY` | Flask 密钥 | - |
| `JWT_SECRET_KEY` | JWT 密钥 | - |
| `AI_REPORT_PROVIDER` | AI 日报提供商 | siliconflow |
| `SILICONFLOW_API_KEY` | SiliconFlow API 密钥 | - |

### Docker 部署

```bash
docker-compose up -d
```

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

## 默认账户

首次启动自动创建默认管理员：`admin0` / `csac123456`
