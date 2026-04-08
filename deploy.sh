#!/bin/bash

# easytier完整部署脚本（改进版）
# 功能：安装dependencies、部署easytier主服务端、启动Flask应用

# ============== 配置 ==============
NETWORK_NAME="${1:-aly-sh}"
NETWORK_SECRET="${2:-ashdhaw23423}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/root/easytier"
ZIP_NAME="easytier-linux-x86_64-v2.4.5.zip"
ZT_LIST="$INSTALL_DIR/easytier-linux-x86_64"
VENV_DIR="$SCRIPT_DIR/.venv"
CONFIG_FILE="$SCRIPT_DIR/.env"

# ============== 颜色输出 ==============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ============== 权限检查 ==============
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用 root 用户或 sudo 运行此脚本。"
        exit 1
    fi
}

# ============== 保存配置 ==============
save_config() {
    print_info "保存部署配置..."
    cat > "$CONFIG_FILE" << EOF
# easytier 部署配置 - 由deploy.sh自动生成
NETWORK_NAME="$NETWORK_NAME"
NETWORK_SECRET="$NETWORK_SECRET"
INSTALL_DIR="$INSTALL_DIR"
DEPLOY_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
EOF
    print_info "配置已保存到 $CONFIG_FILE"
}

# ============== 系统依赖安装 ==============
install_system_deps() {
    print_info "检查并安装系统依赖..."
    
    # 更新APT缓存
    apt update -qq
    
    # 定义需要的工具
    local tools=("screen" "unzip" "ufw" "wget" "python3" "python3-pip" "python3-venv")
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            if [ "$tool" = "python3-venv" ]; then
                tool="python3.10-venv"  # 适配特定版本
            fi
            print_warning "$tool 未安装，正在安装..."
            apt install -y "$tool" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                print_info "$tool 已安装。"
            else
                print_error "$tool 安装失败。"
            fi
        else
            print_info "$tool 已安装。"
        fi
    done
}

# ============== 防火墙配置 ==============
configure_firewall() {
    print_info "配置 UFW 防火墙规则..."
    
    local ports=(11010 11011 11013 22 5000)  # 添加Flask端口
    
    for port in "${ports[@]}"; do
        ufw allow "$port/tcp" > /dev/null 2>&1
        ufw allow "$port/udp" > /dev/null 2>&1
        print_info "防火墙规则已添加: $port (TCP/UDP)"
    done
    
    # 启用UFW（如果尚未启用）
    ufw_status=$(ufw status | head -n 1)
    if [[ "$ufw_status" != "Status: active" ]]; then
        print_info "启用 ufw 防火墙..."
        echo "y" | ufw enable > /dev/null 2>&1
    else
        print_info "ufw 防火墙已启用。"
    fi
}

# ============== 下载并安装easytier ==============
install_easytier() {
    print_info "安装 easytier 核心..."
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR" || exit 1
    
    # 检查是否已下载
    if [ ! -d "$ZT_LIST" ]; then
        print_info "从远程源下载 easytier..."
        wget -q -O "$ZIP_NAME" "https://soft.surtr.nl/soft/easytier/$ZIP_NAME"
        
        if [ $? -ne 0 ]; then
            print_error "下载失败，请检查网络连接。"
            exit 1
        fi
        
        print_info "解压 easytier..."
        unzip -q -o "$ZIP_NAME"
        rm -f "$ZIP_NAME"
        chmod -R +x "$INSTALL_DIR"
        print_info "easytier 已安装到 $INSTALL_DIR"
    else
        print_info "easytier 已安装，跳过下载步骤。"
    fi
}

# ============== 启动easytier ==============
start_easytier() {
    print_info "启动 easytier 服务端..."
    
    # 检查 screen 会话是否已存在
    if screen -list | grep -q "\.easytier"; then
        print_warning "screen 会话 'easytier' 已存在，跳过启动。"
        print_info "使用 'screen -r easytier' 查看运行状态。"
    else
        print_info "创建 screen 会话 'easytier'..."
        screen -dmS easytier
        
        # 发送启动命令
        sleep 1
        local cmd="cd '$ZT_LIST' && ./easytier-core -i 0.0.0.0 \
--network-name '$NETWORK_NAME' \
--network-secret '$NETWORK_SECRET' \
--vpn-portal wg://0.0.0.0:11013/10.6.6.0/24 \
--relay-all-peer-rpc"
        
        screen -S easytier -X stuff "$cmd$(printf '\r')"
        print_info "easytier 已在 screen 会话中启动。"
        print_info "使用 'screen -r easytier' 查看运行状态。"
    fi
}

# ============== Python虚拟环境和Flask应用 ==============
setup_python_env() {
    print_info "设置 Python 虚拟环境..."
    
    cd "$SCRIPT_DIR" || exit 1
    
    # 创建虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_info "虚拟环境已创建。"
    else
        print_info "虚拟环境已存在。"
    fi
    
    # 激活虚拟环境并安装依赖
    source "$VENV_DIR/bin/activate"
    
    print_info "安装 Python 依赖..."
    pip install -q -r requirements.txt
    
    print_info "初始化数据库..."
    python3 app.py << EOF
from app import db, create_tables, app
with app.app_context():
    create_tables()
EOF
    
    deactivate
}

# ============== 启动Flask应用 ==============
start_flask_app() {
    print_info "启动 Flask 应用..."
    
    # 检查 screen 会话
    if ! screen -list | grep -q "\.flask"; then
        print_info "创建 screen 会话 'flask'..."
        screen -dmS flask
        sleep 1
        
        local cmd="cd '$SCRIPT_DIR' && source '$VENV_DIR/bin/activate' && python3 app.py"
        screen -S flask -X stuff "$cmd$(printf '\r')"
        
        print_info "Flask 应用已在 screen 会话中启动。"
        print_info "使用 'screen -r flask' 查看运行状态。"
        print_info "访问地址: http://localhost:5000"
    else
        print_warning "screen 会话 'flask' 已存在，跳过启动。"
        print_info "使用 'screen -r flask' 查看运行状态。"
    fi
}

# ============== 显示部署摘要 ==============
print_summary() {
    print_info "========== 部署摘要 =========="
    echo "网络名称:    $NETWORK_NAME"
    echo "网络密码:    $NETWORK_SECRET"
    echo "easytier路径: $INSTALL_DIR"
    echo "Flask应用:   http://localhost:5000"
    echo ""
    echo "默认管理员: admin / admin123"
    echo ""
    echo "监控命令:"
    echo "  screen -r easytier    # 查看 easytier 运行状态"
    echo "  screen -r flask       # 查看 Flask 运行状态"
    echo ""
    echo "停止命令:"
    echo "  screen -S easytier -X quit"
    echo "  screen -S flask -X quit"
    print_info "========== 部署完成 =========="
}

# ============== 主流程 ==============
main() {
    print_info "开始部署 easytier + Flask 应用..."
    print_info "网络名称: $NETWORK_NAME"
    print_info "网络密码: $NETWORK_SECRET"
    echo ""
    
    check_root
    install_system_deps
    configure_firewall
    save_config
    install_easytier
    start_easytier
    
    sleep 3
    
    setup_python_env
    start_flask_app
    
    print_summary
}

# 执行主流程
main "$@"
