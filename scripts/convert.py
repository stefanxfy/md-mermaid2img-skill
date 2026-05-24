#!/usr/bin/env python3
"""
mermaid-to-image: 将 Markdown 文件中的 Mermaid 代码块转为图片，生成新的 Markdown 文件。

用法:
    python3 convert.py <input.md> [options]

选项:
    --width 1200      输出图片宽度（默认 1200）
    --scale 2         缩放因子（默认 2，即 2x 分辨率）
    --bg white        背景色（默认 white）
    --theme default   Mermaid 主题（default/dark/forest/neutral）
    --fontsize 16px   字体大小（默认 16px）
    --fontfamily      字体族（默认 "PingFang SC, Microsoft YaHei, sans-serif"）
    --keep-mermaid    保留原始 mermaid 代码块（不删除，放在图片后面）
    --format png      输出格式（png/svg/pdf，默认 png）

输出:
    在输入文件同目录下创建 <basename>_mermaid/ 文件夹:
      - <basename>_mermaid/<basename>.md   —— 替换后的 Markdown 文件
      - <basename>_mermaid/images/         —— 转换后的图片文件
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


def check_mmdc():
    """检查 mmdc 是否可用，不可用则尝试安装。"""
    # 尝试多个可能的 mmdc 路径
    mmdc_paths = ["mmdc"]
    # npm global bin 目录
    npm_prefix = subprocess.run(["npm", "config", "get", "prefix"], capture_output=True, text=True, timeout=10)
    if npm_prefix.returncode == 0:
        prefix = npm_prefix.stdout.strip()
        mmdc_paths.append(os.path.join(prefix, "bin", "mmdc"))
    # 常见全局路径
    home = os.path.expanduser("~")
    for p in [
        os.path.join(home, ".npm-global", "bin", "mmdc"),
        os.path.join(home, ".local", "bin", "mmdc"),
        "/usr/local/bin/mmdc",
    ]:
        mmdc_paths.append(p)
    # Apple Silicon Homebrew
    mmdc_paths.append("/opt/homebrew/bin/mmdc")

    for mmdc_cmd in mmdc_paths:
        try:
            result = subprocess.run([mmdc_cmd, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"[OK] mmdc 已安装: {mmdc_cmd} ({result.stdout.strip()})")
                # 记住可用路径
                os.environ["MMDC_PATH"] = mmdc_cmd
                return True
        except FileNotFoundError:
            continue

    print("[INFO] mmdc 未安装，尝试自动安装 @mermaid-js/mermaid-cli ...")
    try:
        env = os.environ.copy()
        env["PUPPETEER_SKIP_DOWNLOAD"] = "true"
        result = subprocess.run(
            ["npm", "install", "-g", "@mermaid-js/mermaid-cli",
             "--registry=https://registry.npmmirror.com"],
            capture_output=True, text=True, timeout=120,
            env=env,
        )
        if result.returncode == 0:
            print("[OK] mmdc 安装成功")
            return True
        else:
            print(f"[ERROR] npm 安装失败:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 安装 mmdc 失败: {e}")
        return False


def extract_mermaid_blocks(content):
    """提取所有 mermaid 代码块，返回列表 [(code, start_offset, end_offset)]"""
    pattern = re.compile(r'(```mermaid\n)(.*?)(```)', re.DOTALL)
    blocks = []
    for match in pattern.finditer(content):
        code = match.group(2).strip()
        blocks.append({
            'code': code,
            'full_match': match.group(0),
            'start': match.start(),
            'end': match.end(),
        })
    return blocks


def write_mmd_file(code, filepath):
    """将 mermaid 代码写入 .mmd 文件。"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(code + '\n')


def get_puppeteer_config():
    """查找可用的 puppeteer 配置文件。"""
    candidates = [
        os.path.expanduser("~/.puppeteer-config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "puppeteer-config.json"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def render_mmd_to_image(mmd_path, img_path, width, scale, bg, theme, config_path):
    """调用 mmdc 将 .mmd 文件渲染为图片。"""
    # 使用检测到的 mmdc 路径（如果有）
    mmdc_cmd = os.environ.get("MMDC_PATH", "mmdc")
    cmd = [
        mmdc_cmd,
        "-i", mmd_path,
        "-o", img_path,
        "-w", str(width),
        "-s", str(scale),
        "-b", bg,
        "-t", theme,
    ]
    if config_path:
        cmd.extend(["-c", config_path])

    # 自动检测 puppeteer 配置（使用系统 Chrome）
    puppeteer_config = get_puppeteer_config()
    if puppeteer_config:
        cmd.extend(["-p", puppeteer_config])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"[WARN] 渲染失败 {mmd_path}: {result.stderr.strip()}")
        return False
    return True


def create_mermaid_config(fontsize, fontfamily, theme):
    """生成 mermaid 配置 JSON 文件。"""
    config = {
        "theme": theme,
        "themeVariables": {
            "fontSize": fontsize,
            "fontFamily": fontfamily,
        },
    }
    return config


def main():
    parser = argparse.ArgumentParser(description='将 Markdown 中的 Mermaid 代码块转为图片')
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('--width', type=int, default=1200, help='输出图片宽度（默认 1200）')
    parser.add_argument('--scale', type=int, default=2, help='缩放因子（默认 2）')
    parser.add_argument('--bg', default='white', help='背景色（默认 white）')
    parser.add_argument('--theme', default='default', help='Mermaid 主题（默认 default）')
    parser.add_argument('--fontsize', default='16px', help='字体大小（默认 16px）')
    parser.add_argument('--fontfamily', default='PingFang SC, Microsoft YaHei, sans-serif', help='字体族')
    parser.add_argument('--keep-mermaid', action='store_true', help='保留原始 mermaid 代码块')
    parser.add_argument('--format', default='png', choices=['png', 'svg', 'pdf'], help='输出格式（默认 png）')
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.isfile(input_path):
        print(f"[ERROR] 文件不存在: {input_path}")
        sys.exit(1)

    # 1. 检查 mmdc
    if not check_mmdc():
        print("[ERROR] mmdc 不可用，请手动安装: npm install -g @mermaid-js/mermaid-cli")
        sys.exit(1)

    # 2. 读取文件
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. 提取 mermaid 块
    blocks = extract_mermaid_blocks(content)
    if not blocks:
        print("[INFO] 未发现 mermaid 代码块，无需转换。")
        sys.exit(0)

    print(f"[INFO] 发现 {len(blocks)} 个 mermaid 代码块")

    # 4. 创建输出目录
    basename = os.path.splitext(os.path.basename(input_path))[0]
    parent_dir = os.path.dirname(input_path)
    output_dir = os.path.join(parent_dir, f"{basename}_mermaid")
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # 5. 写入 mermaid 配置文件
    config = create_mermaid_config(args.fontsize, args.fontfamily, args.theme)
    config_path = os.path.join(output_dir, "mermaid-config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # 6. 逐个提取、渲染、替换
    img_ext = args.format
    replacements = []
    success_count = 0

    for i, block in enumerate(blocks, 1):
        mmd_filename = f"mermaid_{i:02d}.mmd"
        img_filename = f"mermaid_{i:02d}.{img_ext}"
        mmd_path = os.path.join(images_dir, mmd_filename)
        img_path = os.path.join(images_dir, img_filename)

        # 写 .mmd 文件
        write_mmd_file(block['code'], mmd_path)

        # 渲染为图片
        print(f"[INFO] 渲染 {i}/{len(blocks)}: {img_filename} ...")
        ok = render_mmd_to_image(mmd_path, img_path, args.width, args.scale, args.bg, args.theme, config_path)
        if ok:
            success_count += 1
            # 相对路径: images/mermaid_01.png
            rel_img = f"images/{img_filename}"
            if args.keep_mermaid:
                replacement = f"![图 {i}]({rel_img})\n\n{block['full_match']}"
            else:
                replacement = f"![图 {i}]({rel_img})"
            replacements.append({
                'full_match': block['full_match'],
                'replacement': replacement,
            })
        else:
            print(f"[WARN] 第 {i} 个 mermaid 块渲染失败，保留原始代码块")
            replacements.append({
                'full_match': block['full_match'],
                'replacement': block['full_match'],
            })

    # 7. 替换内容，生成新 Markdown
    new_content = content
    for r in replacements:
        new_content = new_content.replace(r['full_match'], r['replacement'], 1)

    output_md = os.path.join(output_dir, f"{basename}.md")
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # 8. 清理临时 .mmd 文件（保留图片和配置）
    for i in range(1, len(blocks) + 1):
        mmd_file = os.path.join(images_dir, f"mermaid_{i:02d}.mmd")
        if os.path.exists(mmd_file):
            os.remove(mmd_file)

    # 9. 汇总
    print(f"\n{'='*50}")
    print(f"[DONE] 转换完成!")
    print(f"  输入: {input_path}")
    print(f"  输出目录: {output_dir}/")
    print(f"  Markdown: {output_md}")
    print(f"  图片目录: {images_dir}/")
    print(f"  成功: {success_count}/{len(blocks)}")
    if success_count < len(blocks):
        print(f"  ⚠ {len(blocks) - success_count} 个块渲染失败，已保留原始 mermaid 代码")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
