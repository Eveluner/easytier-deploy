import io
import os
import ipaddress
import socket
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

# 加载部署配置
load_dotenv('.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-please')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///easytier.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# easytier部署配置
EASYTIER_NETWORK_NAME = os.environ.get('NETWORK_NAME', 'aly-sh')
EASYTIER_NETWORK_SECRET = os.environ.get('NETWORK_SECRET', 'ashdhaw23423')
EASYTIER_SERVER_PORT = 11013
EASYTIER_RELAY_PORT = 11010

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    networks = db.relationship('Network', backref='owner', lazy=True)
    configs = db.relationship('ConfigFile', backref='owner', lazy=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

class Network(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cidr = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ips = db.relationship('IPAddress', backref='network', lazy=True, cascade='all, delete-orphan')
    configs = db.relationship('ConfigFile', backref='network', lazy=True)

class IPAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'), nullable=False)
    ip = db.Column(db.String(50), nullable=False)
    assigned = db.Column(db.Boolean, default=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('config_file.id'))

class ConfigFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'), nullable=False)
    os_type = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_record = db.relationship('IPAddress', backref='config', lazy=True, uselist=False)

    def filename(self):
        name = self.network.name.replace(' ', '_')
        return f"easytier-{self.os_type}-{name}-{self.id}.conf"

def create_tables():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

with app.app_context():
    create_tables()

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('请先登录。', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin():
            flash('管理员权限不足。', 'danger')
            return redirect(url_for('dashboard'))
        return view(*args, **kwargs)
    return wrapped

def get_server_ip():
    """
    获取服务器的外部IP地址
    """
    try:
        # 尝试连接到外部地址来确定本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # 备选方案：获取主机名对应的IP
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def get_gateway_ip(cidr):
    """
    获取网段的网关IP（网段的第一个可用IP）
    """
    try:
        net = ipaddress.IPv4Network(cidr, strict=False)
        return str(next(net.hosts()))
    except Exception:
        return "10.0.0.1"

@app.route('/')
def index():
    user = current_user()
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not username or not email or not password:
            flash('请填写完整信息。', 'warning')
            return render_template('register.html')

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('用户名或邮箱已存在。', 'warning')
            return render_template('register.html')

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录。', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('登录成功。', 'success')
            return redirect(url_for('dashboard'))
        flash('用户名或密码错误。', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('已退出登录。', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    if user.is_admin():
        networks = Network.query.all()
        configs = ConfigFile.query.all()
    else:
        networks = Network.query.filter_by(owner_id=user.id).all()
        configs = ConfigFile.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, networks=networks, configs=configs)

@app.route('/network/create', methods=['GET', 'POST'])
@login_required
def create_network():
    user = current_user()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        cidr = request.form.get('cidr', '').strip()
        password = request.form.get('password', '').strip()
        if not name or not cidr or not password:
            flash('请填写网段名称、CIDR 和密码。', 'warning')
            return render_template('network_create.html', user=user)
        try:
            network_value = ipaddress.IPv4Network(cidr, strict=False)
        except ValueError:
            flash('CIDR 格式不正确。', 'danger')
            return render_template('network_create.html', user=user)
        if network_value.prefixlen < 24 or network_value.prefixlen > 30:
            flash('仅支持 /24 到 /30 的网段。', 'warning')
            return render_template('network_create.html', user=user)
        network = Network(name=name, cidr=str(network_value), password=password, owner_id=user.id)
        db.session.add(network)
        db.session.commit()
        for host in network_value.hosts():
            db.session.add(IPAddress(network_id=network.id, ip=str(host)))
        db.session.commit()
        flash('虚拟网段创建成功。', 'success')
        return redirect(url_for('dashboard'))
    return render_template('network_create.html', user=user)

def get_network(network_id):
    network = Network.query.get_or_404(network_id)
    user = current_user()
    if network.owner_id != user.id and not user.is_admin():
        abort(403)
    return network

@app.route('/network/<int:network_id>')
@login_required
def network_detail(network_id):
    network = get_network(network_id)
    available_ips = IPAddress.query.filter_by(network_id=network.id, assigned=False).limit(20).all()
    assigned_ips = IPAddress.query.filter_by(network_id=network.id, assigned=True).all()
    configs = ConfigFile.query.filter_by(network_id=network.id).all()
    return render_template('network_detail.html', network=network, available_ips=available_ips, assigned_ips=assigned_ips, configs=configs)

@app.route('/config/create', methods=['GET', 'POST'])
@login_required
def create_config():
    user = current_user()
    if request.method == 'POST':
        network_id = request.form.get('network_id')
        os_type = request.form.get('os_type')
        if not network_id or not os_type:
            flash('请选择网段和目标系统。', 'warning')
            return redirect(url_for('create_config'))
        network = get_network(int(network_id))
        ip_record = IPAddress.query.filter_by(network_id=network.id, assigned=False).first()
        if not ip_record:
            flash('该网段没有可用 IP。', 'danger')
            return redirect(url_for('create_config'))
        ip_record.assigned = True
        config = ConfigFile(
            user_id=user.id,
            network_id=network.id,
            os_type=os_type,
            ip_address=ip_record.ip,
            content='',
        )
        db.session.add(config)
        db.session.flush()
        ip_record.assigned_to = config.id
        config.content = generate_config_text(user, network, os_type, ip_record.ip)
        db.session.commit()
        flash('配置文件已生成。', 'success')
        return redirect(url_for('dashboard'))
    if user.is_admin():
        networks = Network.query.all()
    else:
        networks = Network.query.filter_by(owner_id=user.id).all()
    return render_template('config_create.html', user=user, networks=networks)

def generate_config_text(user, network, os_type, ip_address):
    """
    生成平台特定的配置文件
    
    Linux: 生成一键配置脚本
    Windows: 列出所有配置项目
    """
    net = ipaddress.IPv4Network(network.cidr, strict=False)
    gateway = str(next(net.hosts()))
    prefixlen = net.prefixlen
    server_ip = get_server_ip()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    if os_type.lower() == 'linux':
        # Linux: 生成一键配置脚本
        return (
            f"#!/bin/bash\n"
            f"# easytier Linux 一键配置脚本\n"
            f"# 用户: {user.username}\n"
            f"# 网段: {network.name} ({network.cidr})\n"
            f"# 生成时间: {timestamp}\n"
            f"# 分配IP: {ip_address}/{prefixlen}\n"
            f"\n"
            f"# 检查权限\n"
            f"if [ \"$EUID\" -ne 0 ]; then\n"
            f"  echo \"请使用 sudo 运行此脚本\"\n"
            f"  exit 1\n"
            f"fi\n"
            f"\n"
            f"echo '[INFO] 启动 easytier 客户端...'\n"
            f"\n"
            f"# 启动 easytier 核心\n"
            f"./easytier-core \\\n"
            f"  --network-name '{EASYTIER_NETWORK_NAME}' \\\n"
            f"  --network-secret '{EASYTIER_NETWORK_SECRET}' \\\n"
            f"  --peers {server_ip}:{EASYTIER_RELAY_PORT}\n"
            f"\n"
            f"# 配置虚拟网卡\n"
            f"# 您的虚拟IP: {ip_address}\n"
            f"# 网关: {gateway}\n"
            f"# 掩码: {prefixlen}\n"
        )
    else:
        # Windows: 列出所有配置项目
        return (
            f"# easytier Windows 配置指南\n"
            f"# ================================\n"
            f"# 生成时间: {timestamp}\n"
            f"\n"
            f"【基本信息】\n"
            f"用户: {user.username}\n"
            f"网段名称: {network.name}\n"
            f"网段CIDR: {network.cidr}\n"
            f"\n"
            f"【网络配置】\n"
            f"虚拟IP地址: {ip_address}\n"
            f"子网掩码: /{prefixlen}\n"
            f"网关地址: {gateway}\n"
            f"DNS服务器: 8.8.8.8, 8.8.4.4\n"
            f"\n"
            f"【easytier配置】\n"
            f"网络名称: {EASYTIER_NETWORK_NAME}\n"
            f"网络密码: {EASYTIER_NETWORK_SECRET}\n"
            f"连接方式: 手动\n"
            f"\n"
            f"【服务器信息】\n"
            f"服务器地址: {server_ip}\n"
            f"中继端口: {EASYTIER_RELAY_PORT}/UDP\n"
            f"管理门户: {server_ip}:{EASYTIER_SERVER_PORT}\n"
            f"\n"
            f"【配置步骤】\n"
            f"1. 下载并安装 easytier 客户端\n"
            f"2. 创建新的 VPN 连接\n"
            f"3. 输入上述网络名称和网络密码\n"
            f"4. 设置连接方式为\"手动\"\n"
            f"5. 配置服务器地址和端口\n"
            f"6. 配置虚拟IP地址和子网掩码\n"
            f"7. 配置网关和DNS\n"
            f"8. 连接网络\n"
            f"\n"
            f"【常见问题】\n"
            f"Q: 无法连接到网络？\n"
            f"A: 检查防火墙是否放行UDP {EASYTIER_RELAY_PORT} 端口\n"
            f"\n"
            f"Q: 连接后无法访问其他节点？\n"
            f"A: 确认您的IP地址配置是否正确，网络密码是否一致\n"
            f"\n"
            f"Q: 连接不稳定？\n"
            f"A: 检查网络延迟，考虑使用TCP备选连接\n"
        )


@app.route('/config/<int:config_id>/download')
@login_required
def download_config(config_id):
    config = ConfigFile.query.get_or_404(config_id)
    user = current_user()
    if config.user_id != user.id and not user.is_admin():
        abort(403)
    data = io.BytesIO(config.content.encode('utf-8'))
    return send_file(data, as_attachment=True, download_name=config.filename(), mimetype='text/plain')

@app.route('/config/<int:config_id>/delete', methods=['POST'])
@login_required
def delete_config(config_id):
    config = ConfigFile.query.get_or_404(config_id)
    user = current_user()
    if config.user_id != user.id and not user.is_admin():
        abort(403)
    ip_record = IPAddress.query.filter_by(assigned_to=config.id).first()
    if ip_record:
        ip_record.assigned = False
        ip_record.assigned_to = None
    db.session.delete(config)
    db.session.commit()
    flash('配置文件已删除，并释放了IP。', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.order_by(User.username).all()
    networks = Network.query.order_by(Network.name).all()
    ips = IPAddress.query.order_by(IPAddress.ip).all()
    return render_template('admin.html', user=current_user(), users=users, networks=networks, ips=ips)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')
        if not username or not email or not password:
            flash('请填写完整信息。', 'warning')
            return redirect(url_for('admin_create_user'))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('用户名或邮箱已存在。', 'warning')
            return redirect(url_for('admin_create_user'))
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        flash('用户已创建。', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('admin_create_user.html', user=current_user())

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin():
        flash('不能删除管理员账号。', 'warning')
        return redirect(url_for('admin_panel'))
    db.session.delete(user)
    db.session.commit()
    flash('用户已删除。', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/networks/delete/<int:network_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_network(network_id):
    network = Network.query.get_or_404(network_id)
    db.session.delete(network)
    db.session.commit()
    flash('网段已删除。', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/ip/release/<int:ip_id>', methods=['POST'])
@login_required
@admin_required
def admin_release_ip(ip_id):
    ip = IPAddress.query.get_or_404(ip_id)
    ip.assigned = False
    ip.assigned_to = None
    db.session.commit()
    flash('IP 已释放。', 'success')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
