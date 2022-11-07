import datetime
from dataclasses import asdict, dataclass
from enum import Enum

from tortoise import fields, models, Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator


@dataclass
class Response:
    ok: bool
    message: str
    data: any

    @staticmethod
    def success(message: str, data: any = None):
        r = Response(True, message, data)
        return asdict(r)

    @staticmethod
    def failed(message: str):
        r = Response(False, message, None)
        return asdict(r)


class OperationEnum(str, Enum):
    login = "login"
    apply_container = "apply"
    remove_container = "remove"
    submit_flag = "submit"


class User(models.Model):
    id: int = fields.IntField(pk=True)
    username: str = fields.CharField(max_length=20)
    token: str = fields.CharField(max_length=64, index=True)
    admin: bool = fields.BooleanField(default=False)
    container: fields.ReverseRelation["Container"]
    operations: fields.ReverseRelation["Operation"]
    banned: fields.ReverseRelation["BannedUser"]


class Container(models.Model):
    id: int = fields.IntField(pk=True)
    cid: str = fields.CharField(max_length=64, index=True)
    user: User = fields.OneToOneField("models.User", related_name="container")
    running: bool = fields.BooleanField()
    flag: str = fields.CharField(max_length=42)
    ip: str = fields.CharField(max_length=16)
    port: int = fields.IntField(unique=True)
    time: datetime.datetime = fields.DatetimeField(auto_now_add=True)


class Operation(models.Model):
    id: int = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="operations")
    type: OperationEnum = fields.CharEnumField(OperationEnum)
    ip: str = fields.CharField(max_length=64)
    time: datetime.datetime = fields.DatetimeField(auto_now_add=True)


class BannedUser(models.Model):
    id: int = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation[User] = fields.OneToOneField("models.User", related_name="banned")
    end_time: datetime.datetime = fields.DatetimeField()


class BannedIP(models.Model):
    id: int = fields.IntField(pk=True)
    ip: str = fields.CharField(max_length=64, index=True)
    end_time: datetime.datetime = fields.DatetimeField()


Tortoise.init_models(["models"], "models")
UserOut = pydantic_model_creator(User, name="UserOut", exclude=(
    "token", "admin", "container.cid", "container.user", "container.flag", "container.ip", "operations", "banned"))
ContainerOut = pydantic_model_creator(Container, name="ContainerOut", exclude=("cid", "user", "flag", "ip"))
