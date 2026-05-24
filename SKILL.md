---
name: md-mermaid2img-skill
description: 将 Markdown 文件中的 Mermaid 代码块转换为图片（PNG/SVG/PDF），生成包含图片引用的新 Markdown 文件。当用户需要把包含 Mermaid 图的 Markdown 发布到不支持 Mermaid 渲染的平台（微信公众号、知乎、博客等）时使用。触发场景：(1) 用户说"mermaid 转图片"、"mermaid 渲染"、"导出 mermaid"、(2) 用户要发布含 mermaid 的 Markdown 到公众号/知乎/博客，(3) 用户提到 mmdc 或 mermaid-cli。
---

# Mermaid to Image

将 Markdown 中的 Mermaid 代码块批量渲染为图片，生成可直接发布的新 Markdown 文件。

## 工作流程

1. 确认 mmdc 是否可用，不可用则自动安装
2. 运行 `scripts/convert.py`，传入 Markdown 文件路径
3. 在输入文件同目录生成 `<basename>_mermaid/` 文件夹，内含替换后的 `.md` 和 `images/` 目录

## 使用方法

### 基本用法

```bash
python3 <skill_dir>/scripts/convert.py /path/to/article.md
```

### 常用选项

```bash
# 公众号场景：2x 分辨率 + 白底 + 中文字体
python3 <skill_dir>/scripts/convert.py article.md --width 1200 --scale 2 --bg white --fontsize 16px

# 高清输出（3x）
python3 <skill_dir>/scripts/convert.py article.md --scale 3

# 保留原始 mermaid 代码块（图片 + 代码并存）
python3 <skill_dir>/scripts/convert.py article.md --keep-mermaid

# 输出 SVG（矢量图，可无限放大）
python3 <skill_dir>/scripts/convert.py article.md --format svg
```

### 完整参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input` | (必填) | 输入 Markdown 文件路径 |
| `--width` | 1200 | 输出图片宽度（px） |
| `--scale` | 2 | 缩放因子（2=2x分辨率） |
| `--bg` | white | 背景色 |
| `--theme` | default | Mermaid 主题（default/dark/forest/neutral） |
| `--fontsize` | 16px | 字体大小 |
| `--fontfamily` | PingFang SC, Microsoft YaHei, sans-serif | 字体族 |
| `--keep-mermaid` | false | 保留原始 mermaid 代码块 |
| `--format` | png | 输出格式（png/svg/pdf） |

## 输出结构

```
article.md                    ← 输入文件
article_mermaid/              ← 输出目录
├── article.md                ← 替换后的 Markdown（mermaid 块 → 图片引用）
├── mermaid-config.json       ← 渲染配置
└── images/
    ├── mermaid_01.png
    ├── mermaid_02.png
    └── ...
```

替换规则：
- ` ```mermaid ... ``` ` → `![图 N](images/mermaid_NN.png)`
- 加 `--keep-mermaid` 时：图片引用后保留原始 mermaid 代码块

## 公众号发布注意事项

| 问题 | 解决方案 |
|------|---------|
| 图片模糊 | `--scale 3` 导出 3x 分辨率 |
| 中文发虚/乱码 | 默认已配置 PingFang SC / Microsoft YaHei |
| 图片太大 | `--width 1080 --scale 2` 控制尺寸 |
| 配色不清晰 | 用 `--theme default` + 高对比度 mermaid 配色 |
| 公众号压缩 | 单张 < 2MB，PNG 格式 |

## 依赖

- **Node.js** ≥ 16
- **@mermaid-js/mermaid-cli**（mmdc）— 脚本会自动检测并安装
- **Puppeteer**（mmdc 依赖，自动安装）

## 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| mmdc 安装失败 | npm/网络问题 | 手动 `npm install -g @mermaid-js/mermaid-cli` |
| Chromium 下载失败 | 网络受限 | 设 `PUPPETEER_SKIP_DOWNLOAD=true` 后手动装 Chromium |
| 中文乱码 | 系统缺字体 | 安装字体或用 `--fontfamily` 指定已有字体 |
| 渲染超时 | 图太复杂 | 减少嵌套层级或拆分 |
| subgraph 嵌套布局错乱 | Mermaid 限制 | 减少嵌套层数至 ≤ 3 |
