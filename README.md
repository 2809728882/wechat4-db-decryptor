# WeChat 4.x DB Decryptor

一个只做微信 4.x 数据库解密的命令行工具。

它把本机微信 4.x 的加密数据库解密为普通 SQLite 文件，便于用户备份、审计或后续自行处理自己的数据。本项目不做聊天记录分析、不做媒体导出、不做可视化。

## 功能

- 支持微信 4.x `xwechat_files/.../db_storage` 数据库目录
- 支持自动从已登录的 Windows 微信进程获取数据库密钥
- 支持手动传入 64 位十六进制数据库密钥
- 批量解密 `db_storage` 下的 `.db` 文件
- 输出普通 SQLite 数据库到指定目录
- 默认不在日志里打印密钥

## 环境

- Windows
- Python 3.11+
- 已安装并登录微信 4.x
- 可访问微信数据目录，例如：

```powershell
D:\xwechat_files\wxid_xxxxxxxx_xxxx\db_storage
```

## 安装

推荐使用 `uv`：

```powershell
uv sync
```

如果希望同时安装上游解密后端：

```powershell
uv sync --extra backend
```

本项目依赖 `WeChatDataAnalysis` 的解密模块。开发时可用本地源码路径：

```powershell
$env:WECHAT_DECRYPT_BACKEND_PATH="D:\tools\WeChatDataAnalysis"
```

或安装兼容的上游包后直接运行。

## 使用

自动获取密钥并解密：

```powershell
wechat4-decrypt `
  --db-storage "D:\xwechat_files\wxid_xxxxxxxx_xxxx\db_storage" `
  --wechat-install "D:\Weixin" `
  --out "D:\wechat4-decrypted"
```

使用已有密钥解密：

```powershell
wechat4-decrypt `
  --db-storage "D:\xwechat_files\wxid_xxxxxxxx_xxxx\db_storage" `
  --key-file "D:\keys\wechat_db_key.txt" `
  --out "D:\wechat4-decrypted"
```

解密结果默认位于：

```text
D:\wechat4-decrypted\databases\<account>\*.db
```

## 参数

```text
--db-storage      微信 4.x 账号的 db_storage 目录，必填
--out             解密输出目录，默认 ./decrypted-output
--wechat-install  微信安装目录或 Weixin.exe 路径，自动取密钥时建议提供
--key             64 位十六进制数据库密钥
--key-file        从文件读取数据库密钥
--key-mode        auto、v4 或 hook，默认 v4
--backend-path    WeChatDataAnalysis 源码目录
--save-key-file   将自动获取到的密钥保存到指定文件
```

## 安全说明

本项目仅用于解密你本人设备、本人账号的数据。解密后的 SQLite 文件包含个人隐私，请放在受信任磁盘中，避免上传到公共仓库。

`.gitignore` 已默认排除密钥、数据库、输出目录和日志。

## 许可

本项目代码使用 MIT License。

解密能力依赖上游 `WeChatDataAnalysis` / `wx_key` 等项目，请遵守对应项目的许可证与使用限制。
