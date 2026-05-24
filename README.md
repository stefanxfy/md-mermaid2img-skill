# md-mermaid2img-skill

将 Markdown 文件中的 Mermaid 代码块批量渲染为图片（PNG/SVG/PDF），生成可直接发布的新 Markdown 文件。

适用于把含 Mermaid 图的 Markdown 文章发布到不支持 Mermaid 渲染的平台（微信公众号、知乎、博客等）。

## 特性

- 🔍 自动检测并提取 Markdown 中所有 Mermaid 代码块
- 🖼️ 批量渲染为高清图片（支持 2x/3x 分辨率）
- 📝 生成替换后的 Markdown，mermaid 代码块 → 图片引用
- 🔧 自动检测/安装 mermaid-cli（mmdc）
- 🎨 支持自定义主题、字体、背景色
- 📐 支持 PNG / SVG / PDF 输出格式
- 🔒 渲染失败的块自动保留原始代码，不丢内容

## 安装

### 前置依赖

- **Python 3** ≥ 3.8
- **Node.js** ≥ 16
- **mermaid-cli**（mmdc）— [GitHub](https://github.com/mermaid-js/mermaid-cli)，无需手动安装，脚本会自动检测并安装

### 获取

```bash
git clone git@github.com:stefanxfy/md-mermaid2img-skill.git
```

### 安装到 Agent

本 Skill 支持 OpenClaw、Claude Code 等 AI Agent 框架，安装后可直接用自然语言调用，无需手动执行命令。

**OpenClaw：**

将 Skill 目录复制到 OpenClaw skills 目录即可：

```bash
cp -r md-mermaid2img-skill ~/.qclaw/skills/md-mermaid2img-skill
```

安装后重启 Gateway，Agent 会自动识别。使用时直接说：

> 帮我把 article.md 里的 mermaid 图转成图片

**Claude Code：**

将 Skill 目录放到项目或全局的 `.claude/skills/` 下，Claude Code 会自动加载 SKILL.md。使用时直接说：

> 把这个 md 文件里的 mermaid 转为图片

## 使用方法

### 基本用法（命令行）

```bash
python3 scripts/convert.py /path/to/article.md
```

### 基本用法（Agent 自然语言）

安装到 Agent 后，直接用自然语言描述需求即可：

> 帮我把 `/path/to/article.md` 里的 mermaid 图转成图片

Agent 会自动调用 convert.py 完成转换，你不需要执行任何命令。

执行后会在输入文件同目录生成 `<basename>_mermaid/` 文件夹：

```
article.md                        ← 输入文件
article_mermaid/                  ← 输出目录
├── article.md                    ← 替换后的 Markdown（mermaid 块 → 图片引用）
├── mermaid-config.json           ← 渲染配置
└── images/
    ├── mermaid_01.png
    ├── mermaid_02.png
    └── ...
```

### 公众号场景

公众号图片需要高分辨率 + 白底 + 中文字体：

```bash
python3 scripts/convert.py article.md --width 1200 --scale 2 --bg white
```

如果图片模糊，用 3x 分辨率：

```bash
python3 scripts/convert.py article.md --scale 3
```

### 保留原始 Mermaid 代码

图片 + 源码并存，方便读者复制：

```bash
python3 scripts/convert.py article.md --keep-mermaid
```

### 输出 SVG 矢量图

矢量图可无限放大不失真：

```bash
python3 scripts/convert.py article.md --format svg
```

### 暗色主题

```bash
python3 scripts/convert.py article.md --theme dark
```

## 完整参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input` | （必填） | 输入 Markdown 文件路径 |
| `--width` | 1200 | 输出图片宽度（px） |
| `--scale` | 2 | 缩放因子（2 = 2x 分辨率，3 = 3x） |
| `--bg` | white | 背景色 |
| `--theme` | default | Mermaid 主题（default / dark / forest / neutral） |
| `--fontsize` | 16px | 字体大小 |
| `--fontfamily` | PingFang SC, Microsoft YaHei, sans-serif | 字体族 |
| `--keep-mermaid` | false | 保留原始 mermaid 代码块（图片 + 代码并存） |
| `--format` | png | 输出格式（png / svg / pdf） |

## 公众号发布注意事项

| 问题 | 解决方案 |
|------|---------|
| 图片模糊 | `--scale 3` 导出 3x 分辨率 |
| 中文发虚/乱码 | 默认已配置 PingFang SC / Microsoft YaHei |
| 图片太大 | `--width 1080 --scale 2` 控制尺寸 |
| 配色不清晰 | 用 `--theme default` + 高对比度 Mermaid 配色 |
| 公众号压缩 | 单张 < 2MB，PNG 格式 |

## Mermaid 语法兼容提示

以下写法在 Mermaid 新版中会导致渲染失败，脚本会自动保留原始代码块：

| 问题写法 | 修复方式 |
|---------|---------|
| sequenceDiagram 中的 `style` 指令 | sequenceDiagram 不支持 `style`，需删除 |
| `<br/>` 在 sequenceDiagram 消息文本中 | 改为标点连接或拆成多行 |
| flowchart 节点中 `<br/>` + 特殊字符 | 改为 `\n`，节点文本加引号 |

## 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| mmdc 安装失败 | npm/网络问题 | 手动 `npm install -g @mermaid-js/mermaid-cli` |
| Chromium 下载失败 | 网络受限 | 设 `PUPPETEER_SKIP_DOWNLOAD=true`，配置 `~/.puppeteer-config.json` 使用系统 Chrome |
| 中文乱码 | 系统缺字体 | 安装字体或用 `--fontfamily` 指定已有字体 |
| 渲染超时 | 图太复杂 | 减少嵌套层级或拆分 |
| subgraph 嵌套布局错乱 | Mermaid 限制 | 减少嵌套层数至 ≤ 3 |

## 项目结构

```
md-mermaid2img-skill/
├── README.md              # 本文件
├── SKILL.md               # OpenClaw Skill 定义
└── scripts/
    └── convert.py         # 核心转换脚本
```

## License

MIT
