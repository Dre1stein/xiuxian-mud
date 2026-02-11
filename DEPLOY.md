# 修仙文字MUD - Web部署指南

## 快速启动

### 1. 安装依赖
```bash
pip install flask click
```

### 2. 启动Web服务器
```bash
python start_web_simple.py
```

### 3. 访问游戏
打开浏览器访问：http://localhost:5000

## 部署选项

### 方案一：本地开发（已运行）
- 地址：http://localhost:5000
- 特点：适合开发和测试

### 方案二：局域网访问
修改 `start_web_simple.py` 中的 host：
```python
app.run(host='0.0.0.0', port=5000)
```
然后其他设备可以通过你的IP地址访问：
- http://你的IP:5000

### 方案三：生产部署（Gunicorn）
```bash
# 安装gunicorn
pip install gunicorn

# 使用gunicorn启动（生产环境）
gunicorn -w 4 -b 0.0.0.0:5000 "src.web.simple_app:app"
```

## 功能说明

### Web界面功能
1. **登录/注册**：创建角色，选择门派
2. **角色信息**：显示等级、境界、属性等
3. **打坐修炼**：获得经验和仙石
4. **秘境探索**：随机事件、战斗
5. **战斗系统**：回合制战斗
6. **任务系统**：日常任务和主线任务

### API端点
- `GET /` - 游戏主页
- `GET /login` - 登录页面
- `GET /register` - 注册页面
- `POST /api/player/create` - 创建角色
- `POST /api/player/login` - 登录
- `GET /api/player/status` - 角色状态
- `POST /api/action/cultivate` - 打坐修炼
- `GET /api/sects` - 门派列表

## 数据存储

玩家数据存储在 `data/players/` 目录下，每个玩家一个JSON文件。

## 故障排除

### 端口被占用
```bash
# 查找占用5000端口的进程
lsof -i :5000

# 终止进程
kill -9 <PID>

# 或使用其他端口
python start_web_simple.py --port 8080
```

### 权限问题
```bash
# 确保目录可写
chmod -R 755 data/
```

## 技术支持

如有问题，请检查：
1. Python版本 >= 3.8
2. Flask已安装
3. 端口未被占用
4. 有写入权限

---

**修仙文字MUD v1.0**
*凡人修仙，逆天改命*
