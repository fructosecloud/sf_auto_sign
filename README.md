# SF Auto Sign

> ⚠️ 该项目全部使用AI编写，出现的任何问题我不承担任何责任。


自动签到脚本，使用 GitHub Actions 定时执行。

## 功能

- ✅ 每日自动签到
- ✅ 多端通知（通过 ntfy.sh）
- ✅ 自动保活机制（防止 GitHub Actions 停用）

## 保活机制

项目包含两个 GitHub Actions Workflow：

1. **sign** - 每日执行签到任务
2. **keep_alive** - 每月1号执行，保持仓库活跃

## 设置

1. Fork 本仓库
2. 在仓库 Settings → Secrets → Actions 中添加必要的 Secrets
3. 手动触发一次签到任务测试功能

## Secrets 配置

需要配置以下 Secrets：

- `SF_NONCE`
- `SF_DEVICETOKEN`
- `SF_SIGN`
- `SF_AUTHORIZATION`
- `SF_COOKIE_SFCOMMUNITY`
- `SF_COOKIE_SESSIONAPP`
- `NTFY_TOPIC`
