# 抖音视频合并工具 (Douyin Video Merger)

一个用于下载和合并抖音用户视频的Python工具。支持批量下载指定用户的视频，并按时间顺序合并成一个完整的视频文件。

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/lalaking666/douyin_merger.git
cd douyin_merger

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行安装脚本
python setup.py

# 4. 配置Cookie和用户信息（见下方配置说明）

# 5. 运行程序
python src/core.py
```

## 功能特性

- 🔍 自动获取指定抖音用户的视频列表
- ⬇️ 批量下载视频文件
- 🎬 自动转码视频为统一格式 (1080x1920)
- 🔗 按时间顺序合并视频
- 🚀 多线程并发下载，提高效率
- 📝 智能跳过已下载的视频
- 💾 支持断点续传

## 安装依赖

```bash
# 使用 Poetry 安装依赖
poetry install

# 或者使用 pip 安装
pip install -r requirements.txt
```

## 配置说明

### 1. cookies.json 格式

`cookies.json` 文件包含访问抖音网站所需的Cookie信息，格式如下：

```json
[
  {
    "name": "cookie_name",
    "value": "cookie_value"
  },
  {
    "name": "another_cookie",
    "value": "another_value"
  }
]
```

#### 如何获取 cookies.json

1. 安装 Chrome 扩展 [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor-cookie-mana/hocoakkpjckombahpgmbhpilegeicdeh)
2. 访问 [抖音网站](https://www.douyin.com) 并登录
3. 点击 Cookie Editor 扩展图标
4. 点击 "Export" 按钮，选择 "Export as JSON"
5. 将导出的内容保存为 `src/cookies.json` 文件

**注意**: 项目提供了 `src/cookies.example.json` 作为参考格式。

### 2. config.json 格式

`config.json` 文件包含要下载的用户信息和程序配置：

```json
{
  "users": [
    {
      "nickname": "用户昵称",
      "sec_uid": "用户sec_uid"
    }
  ],
  "ffmpeg_max_workers": 4,
  "store_dir": "data"
}
```

#### 配置项说明

- `users`: 用户列表，每个用户包含 `nickname`（昵称）和 `sec_uid`（用户ID）
- `ffmpeg_max_workers`: FFmpeg转码和合并时使用的最大线程数，默认为4
- `store_dir`: 视频文件存储目录，默认为"data"

#### 如何获取 sec_uid

1. 访问用户的抖音主页
2. 右键点击页面，选择"查看页面源代码"
3. 搜索 `sec_uid`，找到类似 `"sec_uid":"MS4wLjABAAAA..."` 的字符串
4. 复制引号内的值作为 sec_uid

**注意**: 项目提供了 `src/config.example.json` 作为参考格式。

## 使用方法

1. 复制示例配置文件：
   ```bash
   cp src/cookies.example.json src/cookies.json
   cp src/config.example.json src/config.json
   ```

2. 配置 `src/cookies.json` 和 `src/config.json` 文件

3. 运行程序：
   ```bash
   # 使用 Poetry
   poetry run python src/core.py
   
   # 或直接运行
   python src/core.py
   ```

## 项目结构

```
douyin_merger/
├── src/
│   ├── core.py              # 主程序
│   ├── xb.py               # X-Bogus 签名生成
│   ├── cookies.json        # Cookie 配置 (需要用户配置)
│   ├── cookies.example.json # Cookie 配置示例
│   ├── config.json         # 用户配置 (需要用户配置)
│   ├── config.example.json # 用户配置示例
│   └── data/               # 下载的视频文件 (可配置)
├── setup.py                # 安装脚本
├── README.md
├── pyproject.toml
├── poetry.lock
└── requirements.txt
```

## 输出文件

- 下载的视频文件保存在 `src/{store_dir}/{用户昵称}/` 目录下
- 合并后的视频文件保存为 `src/{store_dir}/{用户昵称}.mp4`
- 视频元数据保存为 `src/{store_dir}/{用户昵称}/{视频ID}.json`

## 注意事项

- 请确保网络连接稳定
- 需要安装 ffmpeg 用于视频转码和合并
- 遵守抖音的使用条款和版权规定
- 仅用于个人学习和研究目的
- **重要**: `cookies.json` 和 `config.json` 包含敏感信息，已被添加到 `.gitignore` 中，不会被提交到版本控制

## 依赖要求

- Python 3.10+
- ffmpeg
- 相关Python包（见 pyproject.toml 或 requirements.txt）

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。
