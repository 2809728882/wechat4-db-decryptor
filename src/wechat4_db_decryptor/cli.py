from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import sys
from pathlib import Path


HEX_KEY_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _patch_windows_ctypes_compat() -> None:
    """Keep older upstream key_v4 builds working on Windows."""
    if os.name != "nt":
        return
    try:
        from ctypes import wintypes

        if not hasattr(ctypes, "LPVOID") and hasattr(wintypes, "LPVOID"):
            ctypes.LPVOID = wintypes.LPVOID  # type: ignore[attr-defined]
    except Exception:
        pass


def _add_backend_path(path: str | None) -> None:
    raw = path or os.environ.get("WECHAT_DECRYPT_BACKEND_PATH", "")
    if not raw:
        return
    backend = Path(raw).expanduser().resolve()
    candidates = [backend, backend / "src"]
    for candidate in reversed(candidates):
        if candidate.exists():
            sys.path.insert(0, str(candidate))


def _read_key(args: argparse.Namespace) -> str:
    key = str(args.key or "").strip()
    if args.key_file:
        key = Path(args.key_file).expanduser().read_text(encoding="utf-8").strip()
    if key:
        key = key.lower().removeprefix("0x")
        if not HEX_KEY_RE.fullmatch(key):
            raise SystemExit("数据库密钥格式不正确：需要 64 位十六进制字符串。")
    return key


def _import_backend():
    _patch_windows_ctypes_compat()
    try:
        from wechat_decrypt_tool.key_service import get_db_key_workflow
        from wechat_decrypt_tool.wechat_decrypt import decrypt_wechat_databases
    except Exception as exc:
        raise SystemExit(
            "无法加载 WeChatDataAnalysis 后端。请先安装上游依赖，或设置 "
            "WECHAT_DECRYPT_BACKEND_PATH / --backend-path 指向 WeChatDataAnalysis 源码目录。\n"
            f"原始错误：{exc}"
        ) from exc
    return get_db_key_workflow, decrypt_wechat_databases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wechat4-decrypt",
        description="Decrypt WeChat 4.x encrypted databases to plain SQLite.",
    )
    parser.add_argument("--db-storage", required=True, help="微信账号 db_storage 目录")
    parser.add_argument("--out", default="decrypted-output", help="解密输出目录")
    parser.add_argument("--wechat-install", default="", help="微信安装目录或 Weixin.exe 路径")
    parser.add_argument("--key", default="", help="64 位十六进制数据库密钥")
    parser.add_argument("--key-file", default="", help="从文件读取数据库密钥")
    parser.add_argument("--key-mode", choices=["auto", "v4", "hook"], default="v4", help="自动取密钥模式")
    parser.add_argument("--backend-path", default="", help="WeChatDataAnalysis 源码目录")
    parser.add_argument("--save-key-file", default="", help="将自动获取的密钥保存到指定文件")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    db_storage = Path(args.db_storage).expanduser().resolve()
    if not db_storage.exists() or not db_storage.is_dir():
        raise SystemExit(f"db_storage 目录不存在：{db_storage}")

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    _add_backend_path(args.backend_path)
    get_db_key_workflow, decrypt_wechat_databases = _import_backend()

    os.environ["WECHAT_TOOL_OUTPUT_DIR"] = str(out_dir)
    os.environ.setdefault("WECHAT_TOOL_BUILD_SESSION_LAST_MESSAGE", "0")

    key = _read_key(args)
    key_source = "manual"
    if not key:
        print("[1/2] 自动获取数据库密钥，密钥不会打印到终端。", flush=True)
        key_result = get_db_key_workflow(
            wechat_install_path=args.wechat_install or None,
            db_storage_path=str(db_storage),
            key_mode=args.key_mode,
        )
        key = str(key_result.get("db_key") or "").strip().lower()
        if not HEX_KEY_RE.fullmatch(key):
            raise SystemExit("自动获取数据库密钥失败。")
        key_source = str(key_result.get("method") or args.key_mode)
        if args.save_key_file:
            save_path = Path(args.save_key_file).expanduser().resolve()
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(key, encoding="utf-8")
            print(f"[1/2] 密钥已保存：{save_path}", flush=True)
        else:
            print("[1/2] 已获取数据库密钥，值已脱敏。", flush=True)
    else:
        print("[1/2] 使用手动提供的数据库密钥，值已脱敏。", flush=True)

    print("[2/2] 开始解密数据库。", flush=True)
    result = decrypt_wechat_databases(db_storage_path=str(db_storage), key=key)

    redacted = dict(result)
    redacted["db_key_redacted"] = True
    redacted["db_key_source"] = key_source
    result_path = out_dir / "decrypt_result.json"
    result_path.write_text(json.dumps(redacted, ensure_ascii=False, indent=2), encoding="utf-8")

    status = str(result.get("status") or "")
    success = int(result.get("successful_count") or 0)
    total = int(result.get("total_databases") or 0)
    output_directory = str(result.get("output_directory") or out_dir)
    print(f"[完成] 状态：{status}，成功：{success}/{total}", flush=True)
    print(f"[完成] 输出目录：{output_directory}", flush=True)
    print(f"[完成] 结果文件：{result_path}", flush=True)
    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
