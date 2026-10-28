from typing import Any


class Table:
    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def table_name() -> str:
        raise NotImplementedError
