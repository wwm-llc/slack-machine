from __future__ import annotations
import logging

from machine.models.core import Manual, HumanHelp
from machine.plugins.base import MachineBasePlugin
from machine.plugins.message import Message
from machine.plugins.decorators import respond_to
from machine.plugins.admin_utils import matching_roles_by_user_id

logger = logging.getLogger(__name__)


class HelpPlugin(MachineBasePlugin):
    """Getting Help"""

    @respond_to(r"^help$")
    async def help(self, msg: Message) -> None:
        """help: display this help text"""
        manual: Manual | None = await self.storage.get("manual", shared=True)
        if manual is None:
            help_text = "Help is not available!"
        else:
            help_text = "This is what I can respond to:\n\n"
            help_text += "\n\n".join([self._gen_class_help_text(cls, fns) for cls, fns in manual.human.items() if fns])
        await msg.say(help_text)

    @respond_to(r"^robot help$")
    async def robot_help(self, msg: Message) -> None:
        """robot help: display regular expressions that the bot responds to"""
        manual: Manual | None = await self.storage.get("manual", shared=True)
        if manual is None:
            help_text = "Help is not available!"
        else:
            help_text = "This is what triggers me:\n\n"
            help_text += "\n\n".join(
                [self._gen_class_robot_help(cls, regexes) for cls, regexes in manual.robot.items()]
            )
        await msg.say(help_text)

    def _gen_class_help_text(self, class_help: str, fn_helps: dict[str, HumanHelp]) -> str:
        help_text = f"*{class_help}:*\n"
        fn_help_texts = "\n".join([self._gen_help_text(fn_help) for fn_help in fn_helps.values()])
        help_text += fn_help_texts
        return help_text

    def _gen_help_text(self, fn_help: HumanHelp) -> str:
        return f"\t*{fn_help.command}:* {fn_help.help}"

    def _gen_class_robot_help(self, class_help: str, regexes: list[str]) -> str:
        help_text = f"*{class_help}:*\n"
        regex_helps = "\n".join([self._gen_bot_regex(regex) for regex in regexes])
        help_text += regex_helps
        return help_text

    def _gen_bot_regex(self, regex: str) -> str:
        bot_name = self.bot_info["name"]
        actual_bot_mention = regex.replace("@botname", f"@{bot_name}")
        return f"\t`{actual_bot_mention}`"


class RoleAwareHelp(MachineBasePlugin):
    """Getting Help"""

    @respond_to(r"^help$")
    async def help(self, msg: Message) -> None:
        """help: display this help text"""
        manual: Manual | None = await self.storage.get("manual", shared=True)
        user_id = msg.sender.id
        if manual is None:
            help_text = "Help is not available!"
        else:
            help_text = "This is what I can respond to:\n\n"
            help_text += "\n\n".join(
                [await self._gen_class_help_text(cls, fns, user_id) for cls, fns in manual.human.items() if fns])
        await msg.say(help_text, ephemeral=True)

    @respond_to(r"^robot help$")
    async def robot_help(self, msg: Message) -> None:
        """robot help: display regular expressions that the bot responds to"""
        manual: Manual | None = await self.storage.get("manual", shared=True)
        if manual is None:
            help_text = "Help is not available!"
        else:
            help_text = "This is what triggers me:\n\n"
            help_text += "\n\n".join(
                [self._gen_class_robot_help(cls, regexes) for cls, regexes in manual.robot.items()]
            )
        await msg.say(help_text, ephemeral=True)

    async def _gen_class_help_text(self, class_help: str, fn_helps: dict[str, HumanHelp], user_id: str) -> str:

        help_text = f"*{class_help}:*\n"
        fn_help_texts = []
        for fn_help in fn_helps.values():
            text = await self._gen_help_text(fn_help, user_id)
            if text:
                fn_help_texts.append(text)
        help_text += "\n".join(fn_help_texts)
        return help_text

    async def _gen_help_text(self, fn_help: HumanHelp, user_id: str) -> str | None:
        if fn_help.required_any_roles:
            if not await matching_roles_by_user_id(self, user_id, fn_help.required_any_roles):
                # User does not have a required role for this function.
                return ""
        elif fn_help.required_all_roles:
            if not await matching_roles_by_user_id(self, user_id, fn_help.required_all_roles) == len(
                fn_help.required_all_roles):
                # User does not have a required role for this function.
                return ""

        return f"\t*{fn_help.command}:* {fn_help.help}"

    def _gen_class_robot_help(self, class_help: str, regexes: list[str]) -> str:
        help_text = f"*{class_help}:*\n"
        regex_helps = "\n".join([self._gen_bot_regex(regex) for regex in regexes])
        help_text += regex_helps
        return help_text

    def _gen_bot_regex(self, regex: str) -> str:
        bot_name = self.bot_info["name"]
        actual_bot_mention = regex.replace("@botname", f"@{bot_name}")
        return f"\t`{actual_bot_mention}`"
