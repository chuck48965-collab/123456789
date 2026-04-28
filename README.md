# 123456789
# 数据复现 - 邻域类型聚类和AI驱动的地理人口分类

这是一个基于Dash的Web应用程序，用于邻域类型聚类和多种社科数据分析。

## 功能特性

- **数据上传**：用户可以上传自己的CSV数据文件，使用相同的模型进行分析。
- **多种分析类型**：
  - 聚类分析：K-Means聚类与PCA可视化
  - 描述性统计：均值、中位数、标准差等
  - 相关性分析：变量间相关矩阵热力图
  - 简单线性回归：双变量回归分析
  - 多元线性回归：多变量回归模型
  - 散点图：变量关系可视化
  - 直方图：变量分布分析
  - 箱线图：变量分布比较
- **变量选择**：灵活选择分析变量
- **州级分析**：聚类分析支持按州过滤
- **AI命名**：使用Doubao AI为聚类生成描述性名称和描述。
- **响应式界面**：使用Dash Bootstrap Components构建的美观界面。

## 数据格式要求

上传的CSV文件必须包含以下列：
- `GISJOIN`: 地理标识符
- `STATE`: 州代码
- `COUNTY`: 县代码
- `YEAR`: 年份
- `NAME_E`: 名称
- `AQQIE001`: 收入数据
- `AQP5E001`, `AQP5E007` to `AQP5E017`: 教育数据
- `AQQOE001`, `AQQOE003`: 就业数据
- `AQQKE001`, `AQQKE002`: 人口多样性数据（计算为非白人比例）

## 安装和运行

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用：
   ```bash
   python app.py
   ```
   或者后台模式启动服务器（关闭当前进程后仍可访问）：
   ```bash
   python app.py --detach
   ```

3. 在浏览器中访问 `http://127.0.0.1:8050/`

## 正式部署

本项目可部署到支持 Python Web 服务器的云平台（例如 Render、Railway、Fly.io 等）。

- 已添加 `gunicorn` 依赖。
- 生产启动命令：`gunicorn app:server`
- 如果使用平台托管服务，请创建 `Procfile`：
  ```text
  web: gunicorn app:server
  ```

> `app.py` 已支持在 Gunicorn 中运行，添加了 `server = app.server` 供生产服务器加载。

详细部署步骤请参考 [deployment-guide.md](deployment-guide.md)。

## 环境变量

- `DOUBAO_API_KEY`: Doubao API密钥（用于AI命名功能）
- `DOUBAO_MODEL`: Doubao模型名称（默认: ark-313c37df-5144-4a39-b675-d71e54e48932-d871c）

## 项目结构

- `app.py`: 主Dash应用程序
- `data_preprocessing.py`: 数据预处理模块
- `clustering.py`: 聚类和PCA模块
- `llm_naming.py`: AI命名模块
- `analysis.py`: 其他社科分析模块
- `acs_data/`: 默认数据目录
- `cache/`: 缓存目录
- `requirements.txt`: 依赖列表

## 分析类型说明

### 聚类分析
- 使用K-Means算法对标准化变量进行聚类
- PCA降维到2D进行可视化
- AI生成聚类名称和描述

### 描述性统计
- 计算选中变量的描述性统计量
- 包括均值、中位数、标准差、最小值、最大值等

### 相关性分析
- 计算变量间的皮尔逊相关系数
- 热力图可视化相关矩阵

### 回归分析
- 简单线性回归：分析两个变量间的线性关系
- 多元线性回归：分析多个自变量对因变量的影响

### 可视化分析
- 散点图：探索变量间关系
- 直方图：查看变量分布
- 箱线图：比较变量分布特征

## 优化改进

- 添加了多种社科分析功能
- 界面全部汉化
- 标题改为"数据复现"
- 改进错误处理和用户反馈
- 使用Bootstrap组件优化UI
- 延迟加载数据以提高启动速度
- 灵活的变量选择机制