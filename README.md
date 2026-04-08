# easytier-deploy

一个用于管理和分发 easytier 组网配置的基础平台。

## 功能

- 用户注册 / 登录
- 普通用户可创建虚拟网段、生成 Linux / Windows 配置文件
- 自动管理网段内 IP，防止冲突
- 管理员拥有普通用户权限，并可添加/删除用户、管理所有网段和 IP

## 快速启动

1. 创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 初始化数据库（首次运行）：

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

3. 启动服务：

```bash
python app.py
```

4. 在浏览器访问：

```text
http://127.0.0.1:5000
```

默认管理员账号：

- 用户名：`admin`
- 密码：`admin123`

请启动后尽快修改默认密码。

## 数据库迁移

当模型更改时，使用以下命令迁移数据库：

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```
