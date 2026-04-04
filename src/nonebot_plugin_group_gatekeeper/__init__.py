import json
from typing import Any
from pathlib import Path

from nonebot import require, get_driver, on_command, on_request
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from nonebot.permission import SUPERUSER, Permission
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_OWNER,
    Bot,
    Message,
    MessageSegment,
    GroupMessageEvent,
    GroupRequestEvent,
)

require("nonebot_plugin_user_perm")

require("nonebot_plugin_localstore")

import nonebot_plugin_user_perm as upm
from nonebot_plugin_localstore import get_plugin_data_dir

__plugin_meta__ = PluginMetadata(
    name="群聊进群申请管理",
    description="监听加群请求并通知管理员，通过指令同意/拒绝申请",
    usage=(
        "/群管列表 - 查看bot在线时收到的进群申请： \n\n"
        "/群管 同意/拒绝 [编号] - 手动处理进群申请 \n\n"
        "/群管删除 [编号] 或 /群管删除 全部 - 删除进群申请记录(记录仅为bot保存的数据) \n\n"
        "/群管帮助 - 查看群管所有指令"
    ),
    type="application",  # library
    homepage="https://github.com/dontdot/nonebot-plugin-group-gatekeeper",
    supported_adapters={"~onebot.v11"},  # 仅 onebot
    extra={"author": "dontdot 55482264+dontdot@users.noreply.github.com"},
)


driver = get_driver()


class GroupRequestInfo:
    def __init__(
        self,
        request_id: str,
        user_id: int,
        nickname: str,
        avatar_url: str,
        group_id: int,
        flag: str,
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.nickname = nickname
        self.avatar_url = avatar_url
        self.group_id = group_id
        self.flag = flag
        self.status = "pending"
        self.create_time: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "group_id": self.group_id,
            "flag": self.flag,
            "status": self.status,
            "create_time": self.create_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroupRequestInfo":
        obj = cls(
            request_id=data["request_id"],
            user_id=data["user_id"],
            nickname=data["nickname"],
            avatar_url=data["avatar_url"],
            group_id=data["group_id"],
            flag=data["flag"],
        )
        obj.status = data.get("status", "pending")
        obj.create_time: int | None = data.get("create_time")
        return obj


class RequestStorage:
    def __init__(self):
        self.requests: list[GroupRequestInfo] = []
        self._load()

    def _get_data_path(self) -> Path:
        try:
            data_dir = get_plugin_data_dir()
        except Exception:
            data_dir = Path("data") / "nonebot_plugin-group-gatekeeper"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "group_requests.json"

    def _load(self):
        path = self._get_data_path()
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                self.requests = [GroupRequestInfo.from_dict(item) for item in data]
            except Exception as e:
                logger.error(f"加载请求数据失败: {e}")
                self.requests = []

    def _save(self):
        path = self._get_data_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    [req.to_dict() for req in self.requests],
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"保存请求数据失败: {e}")

    def add_request(self, req: GroupRequestInfo) -> None:
        existing = [
            r
            for r in self.requests
            if r.user_id == req.user_id
            and r.group_id == req.group_id
            and r.status == "pending"
        ]
        for r in existing:
            self.requests.remove(r)
        self.requests.append(req)
        self._save()

    async def cleanup_joined_users(self, bot: Bot):
        cleaned_count = 0
        for req in self.requests.copy():
            if req.status != "pending":
                self.requests.remove(req)
                cleaned_count += 1
                continue
            try:
                member_info = await bot.get_group_member_info(
                    group_id=req.group_id, user_id=req.user_id
                )
                if member_info:
                    self.requests.remove(req)
                    cleaned_count += 1
                    logger.info(
                        f"清理已入群用户: {req.user_id} in group {req.group_id}"
                    )
            except Exception:
                pass
        if cleaned_count > 0:
            self._save()
        logger.info(f"启动时清理完成，共清理 {cleaned_count} 条记录")

    def get_pending_requests(self) -> list[GroupRequestInfo]:
        return [req for req in self.requests if req.status == "pending"]

    def get_pending_by_group(self, group_id: int) -> list[GroupRequestInfo]:
        return [
            req
            for req in self.requests
            if req.status == "pending" and req.group_id == group_id
        ]

    def get_request_by_id(self, request_id: str) -> GroupRequestInfo | None:
        for req in self.requests:
            if req.request_id == request_id:
                return req
        return None

    def get_request_by_index(self, index: int) -> GroupRequestInfo | None:
        pending = self.get_pending_requests()
        if 0 <= index < len(pending):
            return pending[index]
        return None

    def update_status(self, request_id: str, status: str):
        req = self.get_request_by_id(request_id)
        if req:
            req.status = status
            self._save()

    def remove_request(self, request_id: str):
        self.requests = [req for req in self.requests if req.request_id != request_id]
        self._save()


storage = RequestStorage()


async def cleanup_on_startup():
    """插件启动时清理已入群用户"""
    try:
        global driver
        bots = driver.bots
        if bots:
            bot = next(iter(bots.values()))
            await storage.cleanup_joined_users(bot)
    except Exception as e:
        logger.error(f"启动清理失败: {e}")


driver.on_bot_connect(cleanup_on_startup)


async def get_user_info(bot: Bot, user_id: int) -> tuple[str, str]:
    try:
        user_info = await bot.get_stranger_info(user_id=user_id)
        nickname = user_info.get("nickname", str(user_id))
        avatar_url = f"https://q.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
        return nickname, avatar_url
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return str(user_id), ""


group_request_matcher = on_request(priority=1)


@group_request_matcher.handle()
async def handle_group_request(bot: Bot, event: GroupRequestEvent, state: T_State):
    if event.sub_type != "add":
        return

    group_id = event.group_id
    user_id = event.user_id
    flag = event.flag

    nickname, avatar_url = await get_user_info(bot, user_id)

    import time

    request_id = f"{group_id}_{user_id}_{int(time.time())}"
    req = GroupRequestInfo(
        request_id=request_id,
        user_id=user_id,
        nickname=nickname,
        avatar_url=avatar_url,
        group_id=group_id,
        flag=flag,
    )
    req.create_time = int(time.time())
    storage.add_request(req)

    pending_list = storage.get_pending_requests()
    index = pending_list.index(req) + 1

    users = (await group_admin_mem(bot, event)) + await upm.get_users(
        event.group_id, mode=1
    )

    msg = Message(
        [
            MessageSegment.text("📢 新的进群申请\n"),
            MessageSegment.text(f"QQ号：{user_id}\n"),
            MessageSegment.text(f"昵称：{nickname}\n"),
            MessageSegment.image(avatar_url),
            MessageSegment.text(f"\n编号：[{index}]\n"),
            MessageSegment.text("━━━━━━━━━━━━━━\n"),
            MessageSegment.text("处理指令：\n"),
            MessageSegment.text(f"  同意：/群管 同意 {index} \n"),
            MessageSegment.text(f"  拒绝：/群管 拒绝 {index} \n"),
            *[MessageSegment.at(id) for id in users if id is not None],
        ]
    )
    await bot.send_group_msg(group_id=group_id, message=msg)


ADMIN_PERMISSION = GROUP_ADMIN | GROUP_OWNER | SUPERUSER | Permission(upm.is_perm_user)

group_admin = on_command("群管", permission=ADMIN_PERMISSION, priority=10, block=True)


@group_admin.handle()
async def handle_admin_command(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    args = args.extract_plain_text().strip().split()
    logger.debug(args)
    if len(args) < 2:
        await group_admin.finish("用法：/群管 同意 [编号]  或  /群管 拒绝 [编号]")

    action = args[0]
    try:
        idx = int(args[1]) - 1
    except ValueError:
        await group_admin.finish("编号必须是数字")

    pending = storage.get_pending_requests()
    if idx < 0 or idx >= len(pending):
        await group_admin.finish(f"无效的编号，当前有 {len(pending)} 个待处理请求")

    req = pending[idx]
    if req.group_id != event.group_id:
        await group_admin.finish("该请求不属于本群，请勿跨群操作")

    try:
        if action == "同意":
            await bot.set_group_add_request(
                flag=req.flag, sub_type="add", approve=True, reason=""
            )
            storage.remove_request(req.request_id)
            result_msg = f"✅ 已同意 {req.nickname}({req.user_id}) 的进群申请"
        elif action == "拒绝":
            await bot.set_group_add_request(
                flag=req.flag,
                sub_type="add",
                approve=False,
                reason="管理员拒绝了您的申请",
            )
            storage.remove_request(req.request_id)
            result_msg = f"❌ 已拒绝 {req.nickname}({req.user_id}) 的进群申请"
        else:
            await group_admin.finish("未知操作，请使用 同意 或 拒绝")
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        await group_admin.finish(f"操作失败：{e}")

    await group_admin.finish(result_msg)


group_list_cmd = on_command(
    "群管列表", permission=ADMIN_PERMISSION, priority=10, block=True
)


@group_list_cmd.handle()
async def handle_list_command(bot: Bot, event: GroupMessageEvent):
    pending = storage.get_pending_by_group(event.group_id)
    if not pending:
        await group_list_cmd.finish("当前没有待处理的进群申请")

    msg = "📋 待处理进群申请列表：\n"
    for i, req in enumerate(pending, 1):
        msg += f"[{i}] {req.nickname}({req.user_id})\n"
    msg += "━━━━━━━━━━━━━━\n"
    msg += f"共 {len(pending)} 条申请"
    await group_list_cmd.finish(msg)


group_delete_cmd = on_command(
    "群管删除", permission=ADMIN_PERMISSION, priority=9, block=True
)


@group_delete_cmd.handle()
async def handle_delete_command(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    args = args.extract_plain_text().strip().split()
    if not args:
        await group_delete_cmd.finish("用法：/群管删除 [编号] 或 /群管删除 全部")

    if args[0] == "全部":
        storage.requests = [
            req for req in storage.requests if req.group_id != event.group_id
        ]
        storage._save()
        await group_delete_cmd.finish("✅ 已删除当前群所有待处理申请")

    try:
        idx = int(args[0]) - 1
    except ValueError:
        await group_delete_cmd.finish("编号必须是数字")

    pending = storage.get_pending_by_group(event.group_id)
    if idx < 0 or idx >= len(pending):
        await group_delete_cmd.finish(f"无效的编号，当前有 {len(pending)} 个待处理请求")

    req = pending[idx]
    storage.remove_request(req.request_id)
    await group_delete_cmd.finish(f"✅ 已删除 {req.nickname}({req.user_id}) 的申请")


group_help_cmd = on_command(
    "群管帮助", permission=ADMIN_PERMISSION, priority=9, block=True
)


@group_help_cmd.handle()
async def handle_group_help(bot: Bot, event: GroupMessageEvent):
    await group_help_cmd.finish(__plugin_meta__.usage)


async def group_admin_mem(bot: Bot, event) -> list:
    try:
        mems = await bot.get_group_member_list(group_id=event.group_id)
        bot_num = (await bot.get_login_info())["user_id"]
        admin_mem = []
        for mem in mems:
            if mem["role"] in ["owner", "admin"] and mem["user_id"] != bot_num:
                admin_mem.append(mem["user_id"])
        return admin_mem
    except Exception as e:
        logger.error(f"获取群管理用户或bot登录号信息出错：\n {e}")
        return []
