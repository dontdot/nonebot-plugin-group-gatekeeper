<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-group-gatekeeper ✨
[![LICENSE](https://img.shields.io/github/license/dontdot/nonebot-plugin-group-gatekeeper.svg)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-group-gatekeeper.svg)](https://pypi.python.org/pypi/nonebot-plugin-group-gatekeeper)
[![python](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13-blue.svg)](https://www.python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
<br/>
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/dontdot/nonebot-plugin-group-gatekeeper/master.svg)](https://results.pre-commit.ci/latest/github/dontdot/nonebot-plugin-group-gatekeeper/master)

</div>

## 📖 介绍

监听群聊的加群请求/邀请事件，并向群内发送申请人信息并@管理人，管理可进行回复来决定申请是否通过

## 💿 安装

<details open>
<summary>【X】使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-group-gatekeeper --upgrade
使用 **pypi** 源安装

    nb plugin install nonebot-plugin-group-gatekeeper --upgrade -i "https://pypi.org/simple"
使用**清华源**安装

    nb plugin install nonebot-plugin-group-gatekeeper --upgrade -i "https://pypi.tuna.tsinghua.edu.cn/simple"


</details>

<details>
<summary>【X】使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>uv</summary>

    uv add nonebot-plugin-group-gatekeeper
安装仓库 master 分支

    uv add git+https://github.com/dontdot/nonebot-plugin-group-gatekeeper@master
</details>

<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-group-gatekeeper
安装仓库 master 分支

    pdm add git+https://github.com/dontdot/nonebot-plugin-group-gatekeeper@master
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-group-gatekeeper
安装仓库 master 分支

    poetry add git+https://github.com/dontdot/nonebot-plugin-group-gatekeeper@master
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_group_gatekeeper"]

</details>

<details>
<summary>【X】使用 nbr 安装(使用 uv 管理依赖可用)</summary>

[nbr](https://github.com/fllesser/nbr) 是一个基于 uv 的 nb-cli，可以方便地管理 nonebot2

    nbr plugin install nonebot-plugin-group-gatekeeper
使用 **pypi** 源安装

    nbr plugin install nonebot-plugin-group-gatekeeper -i "https://pypi.org/simple"
使用**清华源**安装

    nbr plugin install nonebot-plugin-group-gatekeeper -i "https://pypi.tuna.tsinghua.edu.cn/simple"

</details>



## 🎉 使用
### 指令表
| 指令  | 权限  | 需要@ | 范围  |   说明   |
| :---: | :---: | :---: | :---: | :------: |
| `群管列表` | 主人、管理  |  否   | 群聊  | 查看bot在线时收到的进群申请 |
| `群管 同意/拒绝` | 主人、管理  |  否   | 群聊  | 处理进群申请 |
| `群管删除 [编号]` | 主人、管理  |  否   | 群聊  | 删除进群申请记录 |
| `群管帮助` | 主人、管理  |  否   | 群聊  | 查看群管所有指令 |

### 🎨 效果图
如果有效果图的话
