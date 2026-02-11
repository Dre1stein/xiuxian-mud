#!/usr/bin/env python3
"""
修仙文字MUD - Web服务器启动脚本
访问地址: http://localhost:5000
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.web.run_web import app
    print("=" * 60)
    print("🎮 修仙文字MUD Web服务器")
    print("=" * 60)
    print("\n🌐 访问地址:")
    print("   本地: http://localhost:5000")
    print("   网络: http://0.0.0.0:5000")
    print("\n📖 API端点:")
    print("   GET  /api/status     - 服务器状态")
    print("   GET  /api/sects      - 门派列表")
    print("   POST /api/player/create - 创建角色")
    print("   POST /api/player/login  - 登录")
    print("   POST /api/action/cultivate - 打坐修炼")
    print("\n⚠️  按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("\n请确保已安装依赖:")
    print("  pip install flask flask-cors click")
    sys.exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
