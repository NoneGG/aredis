from typing import Any, Dict

from coredis.response.callbacks import SimpleCallback
from coredis.response.types import Command


class CommandCallback(SimpleCallback):
    def transform(self, response: Any) -> Dict[str, Command]:
        commands: Dict[str, Command] = {}

        for command in response:
            if command:
                name = command[0]

                if len(command) >= 6:
                    commands[name] = {
                        "name": name,
                        "arity": command[1],
                        "flags": command[2],
                        "first-key": command[3],
                        "last-key": command[4],
                        "step": command[5],
                        "acl-categories": None,
                        "tips": None,
                        "key-specifications": None,
                        "sub-commands": None,
                    }

                if len(command) >= 7:
                    commands[name]["acl-categories"] = command[6]

                if len(command) >= 8:
                    commands[name]["tips"] = command[7]
                    commands[name]["key-specifications"] = command[8]
                    commands[name]["sub-commands"] = command[9]

        return commands
