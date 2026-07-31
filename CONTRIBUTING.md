# Contributing

欢迎提交和微信 4.x 数据库解密相关的改进。

本项目保持小而专注：

- 接受：解密流程、CLI 参数、错误提示、文档、安全处理
- 不接受：超出数据库解密边界的功能
- 不提交：数据库密钥、解密后的数据库、微信个人数据、日志中的敏感内容

提交前请至少运行：

```powershell
python -m compileall src
python -m wechat4_db_decryptor.cli --help
```
