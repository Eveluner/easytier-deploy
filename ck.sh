#!/bin/bash

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
  echo "请使用 root 用户或 sudo 运行此脚本。"
  exit 1
fi

echo "========== 安装 screen（如未安装） =========="
if ! command -v screen &> /dev/null; then
  echo "screen 未安装，正在安装..."
  apt update
  apt install -y screen
else
  echo "screen 已安装。"
fi

echo "========== 安装 unzip（如未安装） =========="
if ! command -v unzip &> /dev/null; then
  echo "unzip 未安装，正在安装..."
  apt update
  apt install -y unzip
else
  echo "unzip 已安装。"
fi

echo "========== 安装 ufw（如未安装） =========="
if ! command -v ufw &> /dev/null; then
  echo "ufw 未安装，正在安装..."
  apt install -y ufw
else
  echo "ufw 已安装。"
fi

echo "========== 配置 ufw 防火墙规则 =========="
PORTS=(11010 11011 11013 22)

for port in "${PORTS[@]}"; do
  ufw allow $port/tcp
  ufw allow $port/udp
done

# 启用 UFW（如果尚未启用）
ufw_status=$(ufw status | head -n 1)
if [[ "$ufw_status" != "Status: active" ]]; then
  echo "启用 ufw 防火墙..."
  ufw --force enable
else
  echo "ufw 防火墙已启用。"
fi

echo "========== 启动 screen 会话并运行 easytier =========="
# 检查 screen 会话是否已存在
if ! screen -list | grep -q "\.easytier"; then
  echo "正在创建 screen 会话 'easytier'..."
  screen -dmS easytier
else
  echo "screen 会话 'easytier' 已存在，直接使用。"
fi

# 定义变量
INSTALL_DIR="/root/easytier"
ZIP_NAME="easytier-linux-x86_64-v2.4.5.zip"
ZT_LIST="$INSTALL_DIR/easytier-linux-x86_64"

# 定义要发送给 screen 的命令
commands=(
  "mkdir -p $INSTALL_DIR"
  "cd $INSTALL_DIR"
  "wget -O $ZIP_NAME https://file.surtr.nl/soft/easytier/$ZIP_NAME"
  "unzip -o $ZIP_NAME"
  "rm -f $ZIP_NAME"
  "chmod -R +x $INSTALL_DIR"
  "cd $ZT_LIST"
  "./easytier-core -i 0.0.0.0 --network-name aly-sh --network-secret ashdhaw23423 --vpn-portal wg://0.0.0.0:11013/10.6.6.0/24"
)

# 逐条发送命令到 screen
for cmd in "${commands[@]}"; do
  screen -S easytier -X stuff "$cmd$(printf '\r')"
done

echo " 所有操作已完成，easytier 正在 screen 会话中运行。"
echo " 使用 'screen -r easytier' 查看运行状态。"
