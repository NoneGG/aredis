from typing import Any, Dict

from coredis.response.callbacks import SimpleCallback
from coredis.response.types import Command


class CommandCallback(SimpleCallback):
    def transform(self, response: Any) -> Dict[str, Command]:
        commands = {}

        for command in response:
            if command:
                name = command[0]

                if len(command) >= 6:
                    commands[name] = Command(
                        name=name,
                        arity=command[1],
                        flags=command[2],
                        first_key=command[3],
                        last_key=command[4],
                        step=command[5],
                        acl_categories=None,
                        tips=None,
                        key_specifications=None,
                        sub_commands=None,
                    )

                if len(command) >= 7:
                    commands[name]["acl_categories"] = command[6]

                if len(command) >= 8:
                    commands[name]["tips"] = command[7]
                    commands[name]["key_specifications"] = command[8]
                    commands[name]["sub_commands"] = command[9]

        return commands
