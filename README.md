# 轨道交通信号设备检修平台

面向轨道交通信号机、转辙机、轨道电路、联锁设备的检修计划、故障处置与验收的一体化检修管理后台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/            每个业务模块一个页面
│   ├── src/api/              统一请求封装
│   ├── src/stores/           会话与筛选状态
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/          每个业务模块一组接口
│   ├── app/services/         业务规则与状态流转
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
./run.sh
```

健康检查：`curl http://127.0.0.1:8000/api/health`

> 依赖版本在 `requirements.txt` 里全部锁定（含传递依赖），本地、换机器、
> Docker 构建装出的环境一致；不要写成 `>=` 范围。
> `run.sh` 会识别从别的机器拷来的、无法运行的 `.venv` 并自动重建。

### 前端

```bash
cd frontend
npm ci
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

> 前端依赖锁定在 `package.json` + `package-lock.json`，统一用 `npm ci`
> 按锁文件安装；Docker 构建同样走 `npm ci`。

## 统计口径（固定）

概览卡片、模块列表、模块页统计卡片共用同一套口径，定义在
`backend/app/catalog.py`（前端对应 `frontend/src/modules.ts`）：

- **待处理**：模块状态不是末态（状态序列最后一个）的全部条目；
- **异常量**：状态命中该模块异常状态集合（停用、作废、故障、不合格等）的条目；
- `pending` / `abnormal` 不作为独立数据维护，统一由状态推导，动作流转后自动更新。

示例数据由 `backend/app/seed.py` 按台账**确定性生成**，每模块固定 3 条，
任何机器启动后概览都呈现同一组数字：

| 业务模块 | 今日新增 | 待处理 | 异常量 |
| --- | --- | --- | --- |
| 全部 18 个模块合计 | 54 | 54 | 7 |

概览（`GET /api/overview`）的计数直接取自各模块服务的未筛选列表，
与 `GET /api/<模块>` 列表是同一条取数路径；模块列表响应里的 `stats`
与表格同一次请求返回。口径回归测试见
`backend/app/tests/test_caliber.py`，本地执行：

```bash
cd backend
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest app/tests
```

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 线路区段 | `section` | 线路区段 | 区段编码、区段名称、所属线路 |
| 信号机 | `signal` | 信号机 | 设备编号、设备类型、安装位置 |
| 转辙机 | `switch` | 转辙机 | 设备编号、设备型号、安装道岔 |
| 轨道电路 | `track` | 轨道电路 | 设备编号、制式类型、区段长度 |
| 联锁设备 | `interlock` | 联锁设备 | 设备编号、联锁类型、控制范围 |
| 列车防护 | `atp` | 防护设备 | 设备编号、防护等级、覆盖区段 |
| 检修计划 | `plan` | 检修计划 | 计划编号、检修类型、检修对象 |
| 检修任务 | `task` | 检修任务 | 任务编号、关联计划、检修人员 |
| 故障登记 | `fault` | 设备故障 | 故障编号、发生设备、故障现象 |
| 故障处置 | `dispose` | 处置单 | 处置单号、关联故障、处置措施 |
| 器材领用 | `spare` | 器材领用单 | 领用单号、器材名称、器材规格 |
| 电气测试 | `measure` | 测试单 | 测试单号、测试项目、测试设备 |
| 巡视检查 | `patrol` | 巡视单 | 巡视单号、巡视路线、巡视人员 |
| 天窗作业 | `window` | 天窗计划 | 天窗编号、作业类型、作业区段 |
| 监测报警 | `alarm` | 报警事件 | 报警编号、报警类型、报警等级 |
| 验收确认 | `verify` | 验收单 | 验收单号、关联任务、验收项目 |
| 值班交接 | `shift` | 交接记录 | 交接编号、值班班组、值班人员 |
| 状态评估 | `assess` | 评估记录 | 评估编号、评估对象、评估周期 |

## 约定

- 每个模块的前端页面在 `frontend/src/views/<模块>/index.vue`（仅挂载共享组件
  `components/ModulePage.vue`），后端接口由 `app/routers/factory.py` 统一生成，
  业务规则共用 `app/services/base.py`；模块差异只写在 `app/catalog.py`。
- 列表接口统一返回 `{ items, total, page, size, stats }`，动作接口统一返回 `{ ok, message }`。
- 状态流转、待处理/异常判定只允许在 `app/catalog.py` 改口径，路由层不做业务判断。
