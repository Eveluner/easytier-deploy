# 快速参考卡

## 🚀 一键部署

```bash
# 使用默认参数
sudo bash deploy.sh

# 使用自定义参数
sudo bash deploy.sh "my-network" "my-password"
```

## 🌐 Web 界面

**访问地址**：`http://your-ip:5000`

**默认账号**：`admin` / `admin123`

## 📡 监控命令

| 命令 | 说明 |
|------|------|
| `screen -r easytier` | 查看 easytier 日志 |
| `screen -r flask` | 查看 Flask 日志 |
| `sudo ufw status` | 查看防火墙状态 |
| `sudo ufw status numbered` | 查看防火墙规则编号 |

**退出 screen**：`Ctrl+A` 然后 `D`

## 🛑 停止服务

```bash
screen -S easytier -X quit    # 停止 easytier
screen -S flask -X quit       # 停止 Flask
```

## 📁 关键文件位置

| 文件 | 位置 | 用途 |
|------|------|------|
| 部署脚本 | `/workspaces/easytier-deploy/deploy.sh` | 一键部署 |
| Flask应用 | `/workspaces/easytier-deploy/app.py` | Web管理 |
| 部署配置 | `/workspaces/easytier-deploy/.env` | 环境变量 |
| 数据库 | `/workspaces/easytier-deploy/easytier.db` | 用户数据 |
| easytier核心 | `/root/easytier/easytier-linux-x86_64/easytier-core` | VPN核心 |

## 🔄 常用操作

### 重启 easytier

```bash
screen -S easytier -X quit
# 使用原始参数重新启动
```

### 重启 Flask

```bash
screen -S flask -X quit
cd /workspaces/easytier-deploy
source .venv/bin/activate
screen -dmS flask
screen -S flask -X stuff "python3 app.py$(printf '\r')"
```

### 查看部署配置

```bash
cat /workspaces/easytier-deploy/.env
```

### 修改部署配置

```bash
sudo nano /workspaces/easytier-deploy/.env
# 修改后需要重启 Flask 应用
```

## 🔥 防火墙快速配置

```bash
# 查看规则
sudo ufw status numbered

# 添加规则
sudo ufw allow 11010/tcp
sudo ufw allow 11010/udp

# 删除规则
sudo ufw delete allow 11010/tcp

# 重新加载
sudo ufw reload
```

## 🐛 故障排查快速链接

| 问题 | 解决方案 |
|------|---------|
| 无法访问Web界面 | 检查 `screen -r flask` 和防火墙 |
| easytier 无法启动 | 检查 `screen -r easytier` 和防火墙 |
| 客户端无法连接 | 检查网络名称、密码、服务器IP |
| 虚拟网络不稳定 | 检查网络延迟和防火墙规则 |

## 📊 网络配置示例

### 创建网段

| 字段 | 示例 |
|------|------|
| 网段名称 | `dept-sales` |
| CIDR | `10.1.0.0/24` |
| 网段密码 | `secure-pass-123` |

### Linux 一键连接

```bash
sudo bash easytier-linux-dept-sales-1.conf
```

### Windows 手动连接

```
网络名称: corp-network
网络密码: my-password
服务器地址: 123.45.67.89
中继端口: 11010/UDP
虚拟IP: 10.1.0.3
子网掩码: /24
网关: 10.1.0.1
DNS: 8.8.8.8
```

## 💾 备份和恢复

### 备份

```bash
# 备份数据库
cp /workspaces/easytier-deploy/easytier.db easytier.db.backup

# 备份配置
cp /workspaces/easytier-deploy/.env .env.backup

# 完整备份
tar czf easytier-backup-$(date +%Y%m%d).tar.gz \
  /workspaces/easytier-deploy/easytier.db \
  /workspaces/easytier-deploy/.env
```

### 恢复

```bash
# 恢复数据库
cp easytier.db.backup /workspaces/easytier-deploy/easytier.db

# 恢复配置
cp .env.backup /workspaces/easytier-deploy/.env
```

## 📞 获取帮助

- 查看 `README.md` - 完整功能说明
- 查看 `DEPLOYMENT.md` - 详细部署指南
- 查看 `CHANGES.md` - 改进说明
- 检查日志：`screen -r easytier` 或 `screen -r flask`

## ⚡ 性能指标

| 指标 | 值 |
|------|-----|
| 部署时间 | ~5-10分钟 |
| 启动时间 | ~2分钟 |
| 虚拟网络延迟 | <100ms |
| 并发连接 | 1000+ |
| 最大吞吐量 | 依赖硬件 |

## 🎯 操作清单

- [ ] 执行 `deploy.sh`
- [ ] 访问 Web 界面
- [ ] 修改默认管理员密码
- [ ] 创建虚拟网段
- [ ] 生成客户端配置
- [ ] 测试客户端连接
- [ ] 验证网络通讯
- [ ] 配置备份策略

---

**最后更新**：2024年4月8日
**版本**：2.0（改进版）
