# Neo4j Docker 部署指南（Mac Studio M4）

> 适用于 Apple Silicon（M4）Mac，为 QASystemOnMedicalKG 项目提供 Neo4j 5.x 图数据库。  
> 部署完成后配合 [启动项目.md](./启动项目.md) 执行 `build_medicalgraph.py` 与 `chatbot_graph.py`。

---

## 1. 前置条件

| 项目 | 要求 |
|------|------|
| 系统 | macOS（Apple Silicon M4） |
| Docker | Docker Desktop for Mac（Apple Silicon 版） |
| 内存 | 建议为 Neo4j 容器分配 **4GB+** |
| 磁盘 | 数据卷约 **1–2GB**（本项目图谱规模） |

### 1.1 安装 Docker Desktop

若尚未安装：

1. 前往 [Docker Desktop for Mac (Apple Silicon)](https://docs.docker.com/desktop/setup/install/mac-install/)
2. 下载 **Apple Chip** 版本并安装
3. 启动 Docker Desktop，菜单栏出现 Docker 图标且状态为 **Running**

验证：

```bash
docker --version
docker info | grep -i architecture
```

预期架构为 `aarch64` 或 `arm64`。

---

## 2. 一键启动 Neo4j

在项目目录 `QASystemOnMedicalKG/` 下执行。

### 2.1 创建数据卷（持久化）

```bash
docker volume create neo4j-medical-data
```

### 2.2 启动容器

```bash
docker run -d \
  --name neo4j-medical \
  --restart unless-stopped \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yyh123456 \
  -e NEO4J_server_memory_heap_initial__size=512m \
  -e NEO4J_server_memory_heap_max__size=2G \
  -e NEO4J_server_memory_pagecache_size=512m \
  -v neo4j-medical-data:/data \
  neo4j:5
```

**参数说明：**

| 参数 | 含义 |
|------|------|
| `-p 7474:7474` | Neo4j Browser（Web 管理界面） |
| `-p 7687:7687` | Bolt 协议（Python 程序连接此端口） |
| `NEO4J_AUTH=neo4j/yyh123456` | 用户名/密码，**须与 `.env` 一致** |
| `-v neo4j-medical-data:/data` | 数据持久化，重启不丢数据 |
| `neo4j:5` | 官方镜像，支持 arm64 |

> 密码 `yyh123456` 请与项目根目录 [`.env`](../.env) 中 `NEO4J_PASSWORD` 保持一致。若修改此处，同步修改 `.env`。

### 2.3 等待就绪

Neo4j 首次启动约需 **20–60 秒**：

```bash
docker logs -f neo4j-medical
```

看到类似输出即表示就绪：

```
Started.
Remote interface available at http://localhost:7474/
```

按 `Ctrl+C` 退出日志跟踪。

---

## 3. 验证部署

### 3.1 容器状态

```bash
docker ps --filter name=neo4j-medical
```

`STATUS` 应为 `Up ...`。

### 3.2 端口监听

```bash
lsof -i :7687
lsof -i :7474
```

应有 `com.docke` 或 `docker` 相关进程。

### 3.3 Web 界面

浏览器打开：**http://localhost:7474**

- Connect URL：`neo4j://localhost:7687`
- Username：`neo4j`
- Password：`yyh123456`

登录后可在查询框执行：

```cypher
RETURN 1 AS ok
```

### 3.4 Python 连接测试

```bash
cd QASystemOnMedicalKG
source .venv/bin/activate
python -c "
from graph.client import get_driver
d = get_driver()
d.verify_connectivity()
print('Neo4j 连接成功')
d.close()
"
```

---

## 4. 配置项目 `.env`

确认 [`QASystemOnMedicalKG/.env`](../.env) 内容如下：

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=yyh123456
```

> 使用 `bolt://localhost:7687`，不要用 `neo4j://`（Python 驱动推荐 bolt 协议）。

---

## 5. 导入知识图谱

Neo4j 就绪且连接测试通过后：

```bash
cd QASystemOnMedicalKG
source .venv/bin/activate
python build_medicalgraph.py
```

预期：

- step1 导入节点（约 5–15 分钟）
- step2 导入关系（约 5–15 分钟）
- 终端持续打印 `Disease: xxx / xxx` 等进度

### 5.1 验证图谱规模

在 Neo4j Browser 或 cypher-shell 中执行：

```cypher
MATCH (n) RETURN count(n) AS nodes;
```

预期约 **44,111**。

```cypher
MATCH ()-[r]->() RETURN count(r) AS rels;
```

预期约 **294,149**。

### 5.2 启动问答

```bash
python chatbot_graph.py
```

---

## 6. 常用运维命令

### 停止 / 启动

```bash
docker stop neo4j-medical
docker start neo4j-medical
```

### 查看日志

```bash
docker logs neo4j-medical --tail 100
```

### 进入 cypher-shell

```bash
docker exec -it neo4j-medical cypher-shell -u neo4j -p yyh123456
```

### 清空数据库（重新导入前）

在 cypher-shell 或 Browser 中：

```cypher
MATCH (n) DETACH DELETE n;
```

然后重新运行 `python build_medicalgraph.py`。

### 完全删除（含数据）

```bash
docker stop neo4j-medical
docker rm neo4j-medical
docker volume rm neo4j-medical-data   # 慎用：删除所有图数据
```

---

## 7. 使用 docker compose（可选）

若偏好 `docker compose`，在项目根目录创建 `docker-compose.yml`：

```yaml
services:
  neo4j:
    image: neo4j:5
    container_name: neo4j-medical
    restart: unless-stopped
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/yyh123456
      NEO4J_server_memory_heap_initial__size: 512m
      NEO4J_server_memory_heap_max__size: 2G
      NEO4J_server_memory_pagecache_size: 512m
    volumes:
      - neo4j-medical-data:/data

volumes:
  neo4j-medical-data:
```

启动：

```bash
cd QASystemOnMedicalKG
docker compose up -d
docker compose logs -f neo4j
```

---

## 8. 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| `Connection refused` on 7687 | 容器未启动或未就绪 | `docker start neo4j-medical`，等待日志出现 `Started` |
| `AuthError` / 认证失败 | 密码与 `.env` 不一致 | 统一 `NEO4J_AUTH` 与 `.env` 中的密码 |
| Docker Desktop 未运行 | 菜单栏无 Docker 图标 | 打开 Docker Desktop 应用 |
| M4 上镜像拉取慢 | 网络问题 | 配置 Docker 镜像加速，或重试 `docker pull neo4j:5` |
| 导入时内存不足 | 堆内存过小 | 增大 `NEO4J_server_memory_heap_max__size=4G` 后重建容器 |
| 端口被占用 | 7474/7687 已被占用 | `lsof -i :7687` 查占用进程，或改用 `-p 7688:7687` 并修改 `.env` URI |

### 端口冲突时改用 7688 示例

```bash
docker run -d ... -p 7688:7687 ...
```

`.env` 改为：

```env
NEO4J_URI=bolt://localhost:7688
```

---

## 9. 完整流程速查（Mac Studio M4）

```bash
# 1. 确认 Docker 运行
docker info

# 2. 启动 Neo4j
docker volume create neo4j-medical-data
docker run -d --name neo4j-medical --restart unless-stopped \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yyh123456 \
  -e NEO4J_server_memory_heap_max__size=2G \
  -v neo4j-medical-data:/data \
  neo4j:5

# 3. 等待就绪
docker logs -f neo4j-medical   # 看到 Started 后 Ctrl+C

# 4. 配置并导入
cd QASystemOnMedicalKG
cp .env.example .env           # 若尚未配置
# 编辑 .env 密码为 yyh123456
source .venv/bin/activate
pip install -r requirements.txt
python build_medicalgraph.py

# 5. 启动问答
python chatbot_graph.py
```

---

## 10. 相关文档

| 文档 | 说明 |
|------|------|
| [启动项目.md](./启动项目.md) | 完整项目启动流程 |
| [项目升级.md](./项目升级.md) | 技术栈与架构升级说明 |
| [Neo4j Docker 官方文档](https://neo4j.com/docs/operations-manual/current/docker/) | 官方参考 |
