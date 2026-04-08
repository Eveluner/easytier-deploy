# easytier 完整部署指南

一个完整的 easytier 虚拟网络中继解决方案，包括主服务端和 Flask 网络管理界面。

## 🎯 功能特性

- **一键部署**: 使用改进的 `deploy.sh` 脚本快速部署
- **灵活配置**: 支持自定义网络名称和网络密码
- **平台适配**: Windows 和 Linux 客户端生成不同的配置
- **用户管理**: 完整的用户认证和权限管理系统
- **网络管理**: 创建和管理虚拟网段，自动分配虚拟IP
- **配置生成**: 为客户端自动生成对应平台的配置文件
- **防火墙管理**: 自动配置 UFW 防火墙规则

## 📋 系统要求

- Ubuntu 20.04 LTS 或更新版本
- root 权限或 sudo 权限
- 网络连接（用于下载 easytier）

## 🚀 快速开始

### 1️⃣ 基础部署（使用默认参数）

```bash
sudo bash deploy.sh
```

### 2️⃣ 自定义网络名称和密码部署

```bash
sudo bash deploy.sh "my-network" "my-secure-password"
```

参数说明：
- 第一个参数：网络名称（默认: `aly-sh`）
- 第二个参数：网络密码（默认: `ashdhaw23423`）

### 3️⃣ 部署完成后

部署脚本会自动：
- ✅ 安装系统依赖（screen, unzip, ufw, Python等）
- ✅ 配置防火墙规则
- ✅ 下载并安装 easytier
- ✅ 启动 easytier 中继服务
- ✅ 配置 Python 虚拟环境
- ✅ 初始化数据库
- ✅ 启动 Flask 管理应用

## 🔧 部署后配置

### 访问管理界面

打开浏览器访问：
```
http://服务器IP:5000
```

默认凭证：
- 用户名: `admin`
- 密码: `admin123`

### 重要！首次登陆后立即修改密码

1. 点击"管理员面板" → "创建用户"
2. 创建新的管理员账号
3. 使用新账号登陆后删除默认 admin 账户

## 📊 管理界面功能

### 虚拟网段管理

1. **创建网段**：指定网段名称、CIDR、密码
   - 支持 /24 到 /30 的网段
   - 自动生成可用IP地址

2. **查看网段详情**：
   - 可用IP列表
   - 已分配IP列表
   - 相关配置文件列表

### 配置文件生成

#### Linux 配置（自动生成一键配置脚本）

配置文件包含：
```bash
#!/bin/bash
./easytier-core \
  --network-name 'your-network' \
  --network-secret 'your-password' \
  --peers SERVER_IP:11010
```

使用方式：
```bash
sudo bash easytier-linux-your-network-1.conf
```

#### Windows 配置（列表式配置信息）

配置文件包含：
- 虚拟IP地址
- 子网掩码
- 网关地址
- DNS 服务器
- easytier 网络名称
- easytier 网络密码
- 服务器地址和端口
- 详细的配置步骤
- 常见问题解答

## 🖥️ 监控和管理

### 查看 easytier 运行状态

```bash
screen -r easytier
# 使用 Ctrl+A 然后 D 退出 screen
```

### 查看 Flask 应用运行状态

```bash
screen -r flask
# 使用 Ctrl+A 然后 D 退出 screen
```

### 停止服务

```bash
# 停止 easytier
screen -S easytier -X quit

# 停止 Flask
screen -S flask -X quit
```

### 重新启动服务

```bash
# 重启 easytier
screen -dmS easytier
screen -S easytier -X stuff "cd /root/easytier/easytier-linux-x86_64 && ./easytier-core -i 0.0.0.0 --network-name YOUR-NETWORK --network-secret YOUR-PASSWORD --vpn-portal wg://0.0.0.0:11013/10.6.6.0/24 --relay-all-peer-rpc$(printf '\r')"

# 重启 Flask
cd /workspaces/easytier-deploy
source .venv/bin/activate
screen -dmS flask
screen -S flask -X stuff "python3 app.py$(printf '\r')"
```

## 🔐 防火墙规则

脚本自动配置的 UFW 规则：

| 端口 | 协议 | 用途 |
|------|------|------|
| 11010 | TCP/UDP | easytier 中继端口 |
| 11011 | TCP/UDP | easytier 备选端口 |
| 11013 | TCP/UDP | easytier VPN 门户 |
| 5000 | TCP | Flask 管理界面 |
| 22 | TCP | SSH 访问 |

查看防火墙状态：
```bash
sudo ufw status numbered
```

## 📁 文件结构

```
/workspaces/easytier-deploy/
├── deploy.sh                    # 一键部署脚本
├── app.py                      # Flask 主应用
├── requirements.txt            # Python 依赖
├── .env                        # 部署配置（自动生成）
├── .venv/                      # Python 虚拟环境
├── easytier.db                 # SQLite 数据库
├── instance/                   # Flask 实例文件夹
├── migrations/                 # 数据库迁移文件
├── templates/                  # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── network_create.html
│   ├── network_detail.html
│   ├── config_create.html
│   └── admin.html
└── /root/easytier/            # easytier 安装目录
    └── easytier-linux-x86_64/
        └── easytier-core      # easytier 核心程序
```

## 🐛 故障排查

### 问题：无法连接到 Flask 管理界面

**解决方案：**
1. 检查防火墙是否允许 5000 端口
2. 检查 Flask 是否运行：`screen -r flask`
3. 查看服务器日志，查找错误信息

### 问题：easytier 无法启动

**解决方案：**
1. 检查是否已启用防火墙规则：`sudo ufw status`
2. 检查网络连接：`ping 1.1.1.1`
3. 查看 easytier 日志：`screen -r easytier`

### 问题：虚拟网络连接不稳定

**解决方案：**
1. 检查客户端网络配置是否正确
2. 确认网络名称和密码一致
3. 检查 easytier 服务端是否正常运行
4. 检查网络延迟和带宽

## 🔄 更新和维护

### 更新 easytier

```bash
cd /root/easytier
sudo bash -c '
wget -O easytier-linux-x86_64-latest.zip https://file.surtr.nl/soft/easytier/easytier-linux-x86_64-latest.zip
unzip -o easytier-linux-x86_64-latest.zip
chmod -R +x /root/easytier
'
# 重启 easytier 服务
```

### 备份数据库

```bash
cp /workspaces/easytier-deploy/easytier.db /workspaces/easytier-deploy/easytier.db.backup
```

### 恢复数据库

```bash
cp /workspaces/easytier-deploy/easytier.db.backup /workspaces/easytier-deploy/easytier.db
```

## 📝 API 配置说明

部署配置保存在 `.env` 文件中，由 Flask 应用自动读取：

```env
NETWORK_NAME="aly-sh"
NETWORK_SECRET="ashdhaw23423"
INSTALL_DIR="/root/easytier"
DEPLOY_TIME="2024-01-01 12:00:00"
```

这些配置被用于：
- 为 Linux 客户端生成 easytier 连接命令
- 为 Windows 客户端显示网络参数
- 验证客户端连接

## 🤝 贡献和支持

如遇到问题，请检查：
1. 系统日志：`journalctl -xe`
2. easytier 输出：`screen -r easytier`
3. Flask 输出：`screen -r flask`

## 📄 许可证

本项目采用 MIT 许可证。

## 🎓 参考资源

- [easytier 官方文档](https://github.com/EasyTier/EasyTier)
- [Flask 官方文档](https://flask.palletsprojects.com/)
- [UFW 防火墙指南](https://wiki.ubuntu.com/UncomplicatedFirewall)
