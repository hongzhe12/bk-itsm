# BK-ITSM 本地独立运行审计与改造结果

## 结论

当前分支已经支持在禁止连接蓝鲸 PaaS、CMDB、IAM 和其他蓝鲸 SaaS 的条件下启动原版 BK-ITSM。

已验证的核心链路：

```text
本地 Session 登录
  -> 创建工单
  -> Celery 启动流程
  -> 负责人审批
  -> 管理员审批
  -> 流程结束并关闭工单
```

测试工单 `2` 的最终状态为 `FINISHED`，流程日志包含 `CLOSE_TICKET`。

这不是 `itsm_lite`。工单、流程、服务目录、SLA、任务、触发器、评论、附件等原模块均保留。Standalone 模式只替换或关闭蓝鲸生态依赖边界。

## 技术栈

| 组件 | 当前版本/要求 |
| --- | --- |
| Python | 3.11.10 |
| Django | `>=4.2.26,<4.3` |
| Celery | 5.3.0 |
| Kombu | 5.3.0 |
| Redis Python Client | 5.0.3 |
| celery beat | django-celery-beat 2.7.0，DatabaseScheduler |
| Vue | 2.7 |
| Webpack | 4.47 |
| Node.js | 16.20.2，npm 8.19.4 |

## 运行依赖

必需：

- MySQL
- Redis
- Django Web 进程
- Celery worker
- Celery beat

可选：

- RabbitMQ：当前使用 Redis 作为 Broker，不需要 RabbitMQ。
- Elasticsearch：核心工单链路不依赖；只有启用相关搜索/统计配置时才需要。

附件保存在项目内 `USERRES/`。

## 蓝鲸依赖处理

### PaaS 与登录

- [config/__init__.py](../config/__init__.py) 默认启用 `STANDALONE_MODE`，补齐本地 APP_ID/APP_TOKEN，并将登录入口指向 `/login/`。
- [config/default.py](../config/default.py) 在 Standalone 下移除 BlueApps/PaaS 登录 Middleware，启用 Django ModelBackend 和本地登录 Middleware。
- [common/standalone.py](../common/standalone.py) 为未登录 XHR 返回 401 和 `/login/`，普通页面跳转登录页。
- [templates/standalone/login.html](../templates/standalone/login.html) 提供本地 Session 登录表单。
- [urls.py](../urls.py) 注册 `/login/`。

结论：启动和登录不访问 PaaS。

### IAM

- [itsm/auth_iam/utils.py](../itsm/auth_iam/utils.py) 在 Standalone 下直接放行单资源和批量资源鉴权，授权操作 no-op。
- [itsm/auth_iam/urls.py](../itsm/auth_iam/urls.py) 不注册 IAM dispatcher。

结论：IAM 不可用不会阻断工单核心流程。该放行仅用于本地开发。

### CMDB、用户中心和组织架构

- [adapter/config/sites/open/api.py](../adapter/config/sites/open/api.py) 的批量用户查询改走本地用户表。
- [common/local_users.py](../common/local_users.py) 使用本地 `User/UserProperty` 提供用户信息。
- [itsm/component/utils/client_backend_query.py](../itsm/component/utils/client_backend_query.py) 对 CMDB 业务、用户、部门、SOPS、ESB 查询返回本地数据或空结果。
- [itsm/role/models.py](../itsm/role/models.py) 跳过 CMDB 角色和组织架构远端刷新。

结论：本地管理员和本地用户可登录、提单、审批；CMDB 业务、部门树和企业角色数据为空。

### ESB、APIGW、SOPS、蓝盾

- [itsm/component/esb/backend_component.py](../itsm/component/esb/backend_component.py) 禁止 ESB HTTP 调用。
- [itsm/component/apigw/client/backend_apigateway.py](../itsm/component/apigw/client/backend_apigateway.py) 在 Standalone 下对所有通用 APIGW HTTP 调用统一返回本地空结果。
- [itsm/gateway/urls.py](../itsm/gateway/urls.py) 将用户中心、SOPS、蓝盾网关入口替换为空结果。
- SOPS、蓝盾节点执行器和后台轮询任务在 Standalone 下直接返回，不发起外部请求。
- [itsm/openapi/apps.py](../itsm/openapi/apps.py) 跳过启动时 ESB 公钥请求。

结论：核心工单不依赖这些服务。SOPS、蓝盾等专用节点不可执行，相关入口返回空结果。

### CMSI、通知、BKChat、微信

- [itsm/component/notify.py](../itsm/component/notify.py) 在 Standalone 下不发送 CMSI 通知。
- [itsm/workflow/utils.py](../itsm/workflow/utils.py) 不查询 CMSI 通知渠道。
- [config/local_settings.py](../config/local_settings.py) 关闭 BKChat 和通知。
- [weixin/core/settings.py](../weixin/core/settings.py) 在 Standalone 下禁用微信登录。

结论：通知、BKChat 和微信登录不阻塞工单流转。

### Celery

- [itsm/helper/management/commands/celery.py](../itsm/helper/management/commands/celery.py) 接管 `manage.py celery`。
- `worker -l info -B` 自动拆分 beat 子进程。
- Standalone 默认使用 `solo` pool。当前 macOS 上 Celery 5.3 的 prefork 子进程会报 `fast_trace_task` 解包错误，`solo` 已验证可正常执行。

## 本地配置

敏感配置继续放在被 Git 忽略的 `config/local_settings.py`。

可复制 [config/local_settings.example.py](../config/local_settings.example.py) 并设置：

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_NAME
MYSQL_USER
MYSQL_PASSWORD
REDIS_HOST
REDIS_PORT
REDIS_PASSWORD
REDIS_DB
```

蓝鲸地址默认使用 `127.0.0.1:9` 作为本地断路地址，不会连接现有蓝鲸环境。

## 初始化

```bash
cp config/local_settings.example.py config/local_settings.py
python manage.py migrate --noinput
python manage.py createcachetable django_cache account_cache
python manage.py standalone_setup
```

默认本地管理员为 `admin/admin`，可使用 `STANDALONE_ADMIN_USERNAME` 和 `STANDALONE_ADMIN_PASSWORD` 覆盖。

## 启动

```bash
python manage.py runserver 0.0.0.0:8000
python manage.py celery worker -l info -B
cd frontend/pc && npm run dev
```

PC 前端地址为 `http://127.0.0.1:8004/`，代理到 `http://127.0.0.1:8000/`。

## 验证结果

已经实际完成：

- `python manage.py check`：0 issues。
- Standalone 边界测试：9 项通过。
- 原版工单核心测试：10 项通过。
- 原版工单视图测试：47 项中发现并修复 1 个 APIGW 残留调用，修复后的单测通过。
- 本地管理员登录：成功，Session 中用户为 `admin`。
- PC 前端 Webpack 编译：成功。
- Headless Chrome 打开 PC 前端：自动进入本地 `/login/`，未跳转蓝鲸登录。
- 前端 `/init/` 和服务目录 API 代理：HTTP 200。
- Celery 原始命令：worker 和 beat 均启动，使用 `solo`。
- 真实 HTTP 工单链路：创建、两级审批、流程结束，最终状态 `FINISHED`。

## 当前边界

- IAM 是本地全放行，不具备生产权限隔离能力。
- CMDB 业务、组织架构、企业角色、SOPS 模板、蓝盾流水线、通知和 BKChat 数据为空或关闭。
- 依赖这些外部服务的专用工单节点不能执行。
- 原版核心工单流程、服务目录、SLA、任务、触发器、评论和附件模块仍然保留。
