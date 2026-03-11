#!/usr/bin/env python3
"""火山引擎即梦 4.0 图像生成 CLI 工具。

单任务模式：
  python image.py "提示词" [选项]

批量模式（严格串行，并发=1）：
  python image.py --batch tasks.json [--output DIR] [--json]
"""

import argparse
import base64
import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from auth import load_credentials
from api import submit_task, poll_task

# 批量模式下，两个任务之间的等待间隔（秒）
BATCH_TASK_INTERVAL = 1


def download_file(url: str, output_path: str) -> None:
    """从 URL 下载文件到本地。"""
    req = urllib.request.Request(url)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
        with open(output_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)


def read_image_as_base64(file_path: str) -> str:
    """读取本地图片文件并返回 base64 编码字符串。"""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"图片文件不存在: {file_path}")
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_body(task: dict) -> dict:
    """从任务字典构建 API 请求体。"""
    body = {
        "req_key": "jimeng_t2i_v40",
        "prompt": task["prompt"],
    }

    if task.get("image_urls"):
        body["image_urls"] = task["image_urls"]
    if task.get("image_files"):
        body["binary_data_base64"] = [read_image_as_base64(f) for f in task["image_files"]]

    if task.get("width") and task.get("height"):
        body["width"] = task["width"]
        body["height"] = task["height"]
    elif task.get("size"):
        body["size"] = task["size"]

    if task.get("scale") is not None:
        body["scale"] = task["scale"]
    if task.get("force_single"):
        body["force_single"] = True

    return body


def generate_one(task: dict, output_dir: Path, ak: str, sk: str, label: str = "") -> dict:
    """执行单个图像生成任务（提交 → 轮询 → 下载）。

    Returns:
        {"task_id": str, "files": list[str]} 或 {"task_id": str, "error": str}
    """
    prefix = f"[{label}] " if label else ""

    body = build_body(task)

    print(f"{prefix}正在提交图像生成任务...", file=sys.stderr)
    try:
        task_id = submit_task(body, ak, sk)
    except RuntimeError as e:
        print(f"{prefix}提交失败: {e}", file=sys.stderr)
        return {"task_id": None, "error": str(e)}

    print(f"{prefix}任务已提交, task_id: {task_id}", file=sys.stderr)

    print(f"{prefix}正在等待生成结果...", file=sys.stderr)
    req_json = json.dumps({"return_url": True})
    try:
        result = poll_task("jimeng_t2i_v40", task_id, ak, sk, interval=5, timeout=300, req_json=req_json)
    except RuntimeError as e:
        print(f"{prefix}轮询失败: {e}", file=sys.stderr)
        return {"task_id": task_id, "error": str(e)}

    data = result.get("data", {})

    # 下载保存
    task_output_dir = output_dir / task_id if task_id else output_dir
    task_output_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []

    if data.get("image_urls"):
        for i, url in enumerate(data["image_urls"]):
            filename = str(task_output_dir / f"image_{i + 1}.png")
            print(f"{prefix}正在下载: {filename}", file=sys.stderr)
            download_file(url, filename)
            saved_files.append(filename)
    elif data.get("binary_data_base64"):
        for i, b64 in enumerate(data["binary_data_base64"]):
            filename = str(task_output_dir / f"image_{i + 1}.png")
            with open(filename, "wb") as f:
                f.write(base64.b64decode(b64))
            saved_files.append(filename)

    print(f"{prefix}完成, 共 {len(saved_files)} 张图片", file=sys.stderr)
    return {"task_id": task_id, "files": saved_files}


# ──────────────────────────────────────────────
# 单任务模式
# ──────────────────────────────────────────────


def run_single(args: argparse.Namespace) -> None:
    """单任务模式入口。"""
    ak, sk = load_credentials()

    task = {"prompt": args.prompt}
    if args.image_urls:
        task["image_urls"] = args.image_urls
    if args.image_files:
        task["image_files"] = args.image_files
    if args.size:
        task["size"] = args.size
    if args.width:
        task["width"] = args.width
    if args.height:
        task["height"] = args.height
    if args.scale is not None:
        task["scale"] = args.scale
    if args.force_single:
        task["force_single"] = True

    output_dir = Path(args.output) if args.output else Path(".")
    result = generate_one(task, output_dir, ak, sk)

    if result.get("error"):
        raise RuntimeError(result["error"])

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────────
# 批量模式（严格串行，并发=1）
# ──────────────────────────────────────────────


def run_batch(args: argparse.Namespace) -> None:
    """批量模式入口。逐个处理任务，绝不并行。"""
    ak, sk = load_credentials()

    batch_path = Path(args.batch)
    if not batch_path.exists():
        raise RuntimeError(f"批量任务文件不存在: {args.batch}")

    tasks = json.loads(batch_path.read_text(encoding="utf-8"))
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise RuntimeError("批量任务文件格式错误: 需要一个非空的 JSON 数组")

    total = len(tasks)
    output_dir = Path(args.output) if args.output else Path(".")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"批量模式: 共 {total} 个任务，严格串行执行 (并发=1)", file=sys.stderr)
    print(f"输出目录: {output_dir}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    results = []
    success_count = 0
    fail_count = 0

    for i, task in enumerate(tasks):
        if not isinstance(task, dict) or "prompt" not in task:
            print(f"[{i + 1}/{total}] 跳过: 缺少 prompt 字段", file=sys.stderr)
            results.append({"index": i, "error": "缺少 prompt 字段"})
            fail_count += 1
            continue

        result = generate_one(task, output_dir, ak, sk, label=f"{i + 1}/{total}")
        result["index"] = i
        results.append(result)

        if result.get("error"):
            fail_count += 1
        else:
            success_count += 1

        # 非最后一个任务，等待一小段时间再继续
        if i < total - 1:
            time.sleep(BATCH_TASK_INTERVAL)

    # 汇总
    print("=" * 50, file=sys.stderr)
    print(f"批量完成: 成功 {success_count}, 失败 {fail_count}, 共 {total}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="火山引擎即梦 4.0 图像生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 单任务参数
    parser.add_argument("prompt", nargs="?", help="生成图像的提示词（单任务模式）")
    parser.add_argument("--image-urls", nargs="+", metavar="URL", help="输入图片 URL 列表 (0-10张)")
    parser.add_argument("--image-files", nargs="+", metavar="PATH", help="输入图片本地文件路径列表 (0-10张)")
    parser.add_argument("--size", type=int, help="生成图片面积 (默认 4194304 即 2K)")
    parser.add_argument("--width", type=int, help="生成图片宽度 (需同时指定 --height)")
    parser.add_argument("--height", type=int, help="生成图片高度 (需同时指定 --width)")
    parser.add_argument("--scale", type=float, help="文本影响程度 0~1 (默认 0.5)")
    parser.add_argument("--force-single", action="store_true", help="强制只生成 1 张图片")

    # 批量模式
    parser.add_argument("--batch", metavar="FILE", help="批量任务 JSON 文件路径 (严格串行执行)")

    # 通用
    parser.add_argument("--output", "-o", metavar="DIR", help="输出目录 (默认当前目录)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果到 stdout")

    args = parser.parse_args()

    # 互斥校验
    if args.batch and args.prompt:
        parser.error("--batch 和 prompt 不能同时指定")
    if not args.batch and not args.prompt:
        parser.error("请指定 prompt（单任务模式）或 --batch（批量模式）")

    try:
        if args.batch:
            run_batch(args)
        else:
            run_single(args)
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        sys.exit(130)
    except RuntimeError as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
