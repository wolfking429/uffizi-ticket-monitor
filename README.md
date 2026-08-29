# Ticket Availability Monitor

这是一个通用的博物馆门票余票监控器。它通过 GitHub Actions 每 10 分钟检查一次指定日期和时段；当同时满足目标时段与最低票数时，每次检查都会同时发送 PushPlus 微信提醒和邮件，直到手动停用工作流。程序只提醒，不下单、不登录购票账号，也不付款。

## 安全提醒

如果密码、令牌或授权码曾经出现在聊天、截图或公开位置，必须先作废并重新生成，不能继续使用旧值。GitHub 登录密码只能由本人在 GitHub 登录页输入，绝不能放进仓库或 GitHub Secrets。邮件发送必须使用邮箱后台生成的 **SMTP 授权码**，不能使用邮箱登录密码。

仓库可以公开，但所有旅行信息、邮箱地址和凭据都应保存为 GitHub Actions Secrets。代码和工作流不包含这些具体值。

## GitHub Secrets

在仓库的 `Settings → Secrets and variables → Actions → New repository secret` 中逐项添加：

| 名称 | 内容 |
| --- | --- |
| `EVENT_URL` | 官方活动购票页地址 |
| `TARGET_DATE` | 目标日期，格式 `YYYY-MM-DD` |
| `TARGET_TIMES` | 目标时段，以英文逗号分隔，例如 `08:15,08:30` |
| `MIN_TICKETS` | 每个时段所需的最低余票数 |
| `PUSHPLUS_TOKEN` | 重新生成的 PushPlus token |
| `SMTP_USER` | 已开启 SMTP 的发件邮箱；支持 163 邮箱和新浪邮箱 |
| `SMTP_AUTH_CODE` | 邮箱后台生成的 SMTP 授权码 |
| `ALERT_EMAIL` | 接收提醒的邮箱 |

新浪邮箱会按邮箱后缀自动选择官方 SSL 服务器：`@sina.com` 使用 `smtp.sina.com:465`，`@sina.cn`、`@vip.sina.com` 和 `@vip.sina.cn` 也会自动匹配相应服务器。请先在新浪邮箱设置中开启 POP3/SMTP 或 IMAP/SMTP 服务，并使用客户端授权码。

## 启用与测试

1. 打开仓库的 `Actions` 页面，选择 `Ticket monitor`。
2. 点击 `Run workflow`，勾选测试通知后运行。测试消息会明确标记“测试通知”和“不代表真实余票”。
3. 再次手动运行但不要勾选测试通知，确认真实页面检查成功。
4. 定时检查由 GitHub 自动触发。GitHub 的定时任务可能因平台繁忙而延迟几分钟，并不保证精确到秒。

若发现符合条件的票，程序不会记录“已提醒”状态，因此下一次检查仍会继续发送两种提醒。

## 停止监控

进入 `Actions → Ticket monitor`，在右上角菜单中选择 `Disable workflow`。目标日期过去后程序会自动跳过网页检查，但仍建议手动停用工作流。

## 官网拦截说明

购票官网使用浏览器安全验证，可能拒绝数据中心或自动化浏览器。如果运行日志出现 `SiteBlockedError`，表示本次没有得到可信的余票结果，程序不会误报。不要尝试绕过网站安全验证；应保留现有的备用监控，并改用官网允许的访问方式或获得授权的运行环境。

## 本地测试

```text
python -m pip install -e ".[test]"
python -m playwright install chromium
python -m pytest -q
```
