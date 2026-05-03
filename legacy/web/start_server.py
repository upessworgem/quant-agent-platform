#!/usr/bin/env python3
"""
Flask 服务启动脚本
"""

import os
import sys
import argparse

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, logger


def main():
    parser = argparse.ArgumentParser(description='启动股票筛选系统 API 服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='监听端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')

    args = parser.parse_args()

    print(f"""
╔════════════════════════════════════════════════════════╗
║         股票智能筛选系统 - API 服务                    ║
╠════════════════════════════════════════════════════════╣
║  服务地址: http://{args.host}:{args.port:<15}           ║
║  API 文档: http://{args.host}:{args.port}/docs       ║
║  健康检查: http://{args.host}:{args.port}/api/health ║
║  调试模式: {'开启' if args.debug else '关闭':<17}           ║
╚════════════════════════════════════════════════════════╝
""")

    logger.info(f"启动服务: {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
