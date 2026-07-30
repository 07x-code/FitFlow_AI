"""应用依赖装配入口。"""

from app.bootstrap.container import (
    ApplicationContainer,
    create_container,
    get_container,
)

__all__ = ["ApplicationContainer", "create_container", "get_container"]
