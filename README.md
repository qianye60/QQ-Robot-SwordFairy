# 🤖 LLMQ-Horizon Chatbot

一个基于 NoneBot2 和 LangGraph 的Chatbot。

## ✨ 特性

- 🔌 支持多种工具扩展
- 💬 支持群聊和私聊
- 🎯 多种触发方式:
  - @机器人
  - 关键词触发
  - 命令前缀触发
- 🧠 基于 LangGraph 的对话管理
- 📦 自动会话管理和清理



# 安装code_runner的judge0

参考https://github.com/judge0/judge0/blob/master/CHANGELOG.md
我们建议使用 Ubuntu 22.04，在此系统上您需要进行以下 GRUB 更新(改为cgroup v1)：
```
使用 sudo 打开文件 /etc/default/grub
在 GRUB_CMDLINE_LINUX 变量的值中添加 systemd.unified_cgroup_hierarchy=0。
应用更改：sudo update-grub
重启您的服务器：sudo reboot
```
部署步骤:
下载并解压发行版压缩包：
```
wget https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip
unzip judge0-v1.13.1.zip
```
访问[此网站](https://www.random.org/passwords/?num=1&len=32&format=plain&rnd=new)以生成随机密码。
使用生成的密码更新 judge0.conf 文件中的 REDIS_PASSWORD 变量。
再次访问[此网站](https://www.random.org/passwords/?num=1&len=32&format=plain&rnd=new)以生成另一个随机密码。
使用生成的密码更新 judge0.conf 文件中的 POSTGRES_PASSWORD 变量。
运行所有服务并等待几秒钟，直到所有内容都初始化完成：
```
cd judge0-v1.13.1
docker-compose up -d db redis
sleep 10s
docker-compose up -d
sleep 5s
```
您的 Judge0 CE v1.13.1 实例现已启动并运行；访问 http://<您的服务器 IP 地址>:2358/docs 获取文档。