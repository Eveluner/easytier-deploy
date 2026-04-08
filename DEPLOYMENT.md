# 部署指南

## 概述

这项目包含了一个完整的 easytier 部署和管理解决方案，由以下核心组件组成：

1. **deploy.sh** - 一键部署脚本
2. **app.py** - Flask Web 管理应用
3. **.env** - 部署配置（自动生成）

## 快速部署（推荐）

### 使用默认参数部署

```bash
cd /workspaces/easytier-deploy
sudo bash deploy.sh
```

### 使用自定义参数部署

```bash
# deploy.sh <network-name> <network-secret>
sudo bash deploy.sh "my-corp-network" "super-secret-password-123"
```

## 验证部署

部署完成后，检查以下内容：

### 1. 检查 easytier 服务

```bash
screen -r easytier
# 应该能看到类似的输出：
# easytier-core -i 0.0.0.0 --network-name my-corp-network ...
# 按 Ctrl+A 然后 D 退出 screen
```

### 2. 检查 Flask 应用

```bash
screen -r flask
# 应该能看到类似的输出：
# Running on http://0.0.0.0:5000
# 按 Ctrl+A 然后 D 退出 screen
```

### 3. 访问Web界面

打开浏览器访问：
```
http://your-server-ip:5000
```

使用默认凭证登陆：
- 用户名: `admin`
- 密码: `admin123`

## 部署配置详解

### .env 文件

部署脚本会自动创建 `.env` 文件，内容示例：

```env
# easytier 部署配置 - 由deploy.sh自动生成
NETWORK_NAME="my-corp-network"
NETWORK_SECRET="super-secret-password-123"
INSTALL_DIR="/root/easytier"
DEPLOY_TIME="2024-01-15 10:30:00"
```

这些值会被 Flask 应用读取，用于：
- 为 Linux 客户端生成启动命令
- 为 Windows 客户端显示配置信息

### 部署参数说明

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| NETWORK_NAME | 虚拟网络名称 | aly-sh | 否 |
| NETWORK_SECRET | 虚拟网络密码 | ashdhaw23423 | 否 |

## 工作流程

### 1. 部署流程（一次性）

```
deploy.sh
├── 检查 root 权限
├── 安装系统依赖
│   ├── screen
│   ├── unzip
│   ├── ufw
│   ├── wget
│   ├── python3
│   ├── python3-pip
│   └── python3-venv
├── 配置防火墙
│   ├── 允许 11010 (TCP/UDP)
│   ├── 允许 11011 (TCP/UDP)
│   ├── 允许 11013 (TCP/UDP)
│   ├── 允许 5000 (TCP)
│   └── 允许 22 (TCP)
├── 保存配置到 .env
├── 下载并安装 easytier
├── 在 screen 中启动 easytier
├── 配置 Python 虚拟环境
├── 初始化数据库
└── 在 screen 中启动 Flask
```

### 2. 用户操作流程

```
用户登陆
    ↓
创建虚拟网段
    ├── 指定网段名称、CIDR、密码
    └── 系统自动分配IP地址
    ↓
生成客户端配置
    ├── Linux: 下载可执行脚本
    └── Windows: 下载配置说明
    ↓
客户端连接
    ├── Linux: 执行脚本自动连接
    └── Windows: 按步骤手动配置
```

## Linux 客户端配置生成

Flask 应用自动生成的 Linux 配置脚本示例：

```bash
#!/bin/bash
# easytier Linux 一键配置脚本
# 用户: john
# 网段: my-corp-network (10.0.0.0/24)
# 生成时间: 2024-01-15 10:30:00 UTC
# 分配IP: 10.0.0.2/24

if [ "$EUID" -ne 0 ]; then
  echo "请使用 sudo 运行此脚本"
  exit 1
fi

echo '[INFO] 启动 easytier 客户端...'

./easytier-core \
  --network-name 'my-corp-network' \
  --network-secret 'super-secret-password-123' \
  --peers 123.45.67.89:11010

# 配置虚拟网卡
# 您的虚拟IP: 10.0.0.2
# 网关: 10.0.0.1
# 掩码: 24
```

使用方式：

```bash
# 1. 下载配置文件（从 Web 界面或 API）
sudo bash easytier-linux-my-corp-network-1.conf
```

## Windows 客户端配置生成

Flask 应用自动生成的 Windows 配置说明示例：

```
# easytier Windows 配置指南
# ================================
# 生成时间: 2024-01-15 10:30:00 UTC

【基本信息】
用户: john
网段名称: my-corp-network
网段CIDR: 10.0.0.0/24

【网络配置】
虚拟IP地址: 10.0.0.3
子网掩码: /24
网关地址: 10.0.0.1
DNS服务器: 8.8.8.8, 8.8.4.4

【easytier配置】
网络名称: my-corp-network
网络密码: super-secret-password-123
连接方式: 手动

【服务器信息】
服务器地址: 123.45.67.89
中继端口: 11010/UDP
管理门户: 123.45.67.89:11013

【配置步骤】
1. 下载并安装 easytier 客户端
2. 创建新的 VPN 连接
3. 输入上述网络名称和网络密码
4. 设置连接方式为"手动"
5. 配置服务器地址和端口
6. 配置虚拟IP地址和子网掩码
7. 配置网关和DNS
8. 连接网络

【常见问题】
...
```

## 防火墙最小规则集

如果你需要手动配置防火墙而不是使用 UFW：

```bash
# Linux iptables 示例
iptables -A INPUT -p tcp --dport 11010 -j ACCEPT
iptables -A INPUT -p udp --dport 11010 -j ACCEPT
iptables -A INPUT -p tcp --dport 11011 -j ACCEPT
iptables -A INPUT -p udp --dport 11011 -j ACCEPT
iptables -A INPUT -p tcp --dport 11013 -j ACCEPT
iptables -A INPUT -p udp --dport 11013 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# 保存规则（Ubuntu/Debian）
sudo apt install iptables-persistent
sudo netfilter-persistent save
```

## 常见问题解答

### Q: 如何修改已部署的网络名称或密码？

A: 网络名称和密码在部署时指定。如需修改，需要：
1. 停止 easytier 服务
2. 编辑 `.env` 文件
3. 重新启动 easytier

```bash
# 编辑配置
sudo nano /workspaces/easytier-deploy/.env

# 重启服务
screen -S easytier -X quit
# 然后使用新参数重新启动
```

### Q: 如何将现有配置备份？

A: 使用以下命令备份关键数据：

```bash
# 备份数据库
cp easytier.db easytier.db.backup

# 备份配置
cp .env .env.backup

# 创建完整备包
tar czf easytier-backup-$(date +%Y%m%d).tar.gz \
  easytier.db \
  .env \
  instance/
```

### Q: 如何恢复备份？

A: 使用以下命令恢复：

```bash
# 恢复数据库
cp easytier.db.backup easytier.db

# 恢复配置
cp .env.backup .env

# 重启应用
screen -S flask -X quit
screen -dmS flask
screen -S flask -X stuff "cd /workspaces/easytier-deploy && source .venv/bin/activate && python3 app.py$(printf '\r')"
```

### Q: 如何重新初始化数据库？

A: 谨慎使用，这会删除所有用户和网络配置：

```bash
# 备份现有数据库
cp easytier.db easytier.db.old

# 删除现有数据库
rm -f easytier.db

# 重启 Flask 应用
screen -S flask -X quit
screen -dmS flask
screen -S flask -X stuff "cd /workspaces/easytier-deploy && source .venv/bin/activate && python3 app.py$(printf '\r')"
```

## 日志查看

### easytier 日志

```bash
screen -r easytier
# 查看实时日志，按 Ctrl+A 然后 D 退出
```

### Flask 日志

```bash
screen -r flask
# 查看实时日志，按 Ctrl+A 然后 D 退出
```

### 系统日志

```bash
journalctl -u your-service-name -n 50  # 查看最后50行日志
```

## 性能优化建议

### 1. 系统级优化

```bash
# 增加文件描述符限制
sudo ulimit -n 65535

# 增加网络缓冲
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.wmem_max=26214400
```

### 2. easytier 优化

考虑在启动命令中添加：
```bash
./easytier-core \
  --network-name 'my-corp-network' \
  --network-secret 'password' \
  --peers server:11010 \
  --relay-all-peer-rpc \
  -i 0.0.0.0
```

### 3. Flask 优化

对于生产环境，使用 Gunicorn：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 下一步

1. 访问 Web 界面配置第一个虚拟网段
2. 创建用户账号
3. 生成客户端配置
4. 在客户端连接测试

更多帮助请参考 README.md。
