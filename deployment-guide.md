# 云平台部署指南

本项目已准备好部署到正规免费云平台。以下是针对 **Render** 和 **Railway** 的详细部署步骤。

## 通用准备

1. **推送代码到 GitHub**：确保所有更改已提交并推送到 GitHub 仓库。
2. **环境变量**：在平台上设置以下环境变量：
   - `DOUBAO_API_KEY`: 你的 Doubao API 密钥
   - `DOUBAO_MODEL`: Doubao 模型名称（默认: ark-313c37df-5144-4a39-b675-d71e54e48932-d871c）

## Render 部署

1. 访问 [render.com](https://render.com) 并注册账户。
2. 点击 "New" → "Web Service"。
3. 连接你的 GitHub 仓库。
4. 配置服务：
   - **Name**: neighborhood-typology-webapp
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server`
5. 在 "Environment" 部分添加环境变量。
6. 点击 "Create Web Service"。

## Railway 部署

1. 访问 [railway.app](https://railway.app) 并注册账户。
2. 点击 "New Project" → "Deploy from GitHub repo"。
3. 选择你的仓库。
4. Railway 会自动检测 Python 项目并安装依赖。
5. 在项目设置中添加环境变量。
6. 部署完成后，Railway 会提供访问 URL。

## Fly.io 部署（可选）

1. 安装 Fly CLI：`curl -L https://fly.io/install.sh | sh`
2. 登录：`fly auth login`
3. 初始化：`fly launch`（选择 Python 应用）
4. 设置环境变量：`fly secrets set DOUBAO_API_KEY=your_key`
5. 部署：`fly deploy`

## 注意事项

- **免费额度限制**：这些平台有 CPU/内存/流量限制，适合演示用途。
- **数据文件**：确保 `acs_data/acs_data.csv` 已包含在仓库中。
- **缓存目录**：`cache/` 目录会自动创建，无需预先包含。
- **端口**：生产服务器会自动分配端口，无需手动指定。

## 本地测试生产模式

在本地测试 Gunicorn：

```bash
pip install gunicorn
gunicorn app:server
```

访问 `http://127.0.0.1:8000/` 测试。

## 故障排除

- 如果部署失败，检查构建日志中的错误信息。
- 确保所有依赖都在 `requirements.txt` 中。
- 验证环境变量是否正确设置。