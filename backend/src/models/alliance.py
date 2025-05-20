from tortoise.models import Model
from tortoise import fields


class Alliance(Model):
    id = fields.IntField(primary_key=True)
    tag = fields.CharField(max_length=3)

    class Meta:
        table = "alliances"

    def __str__(self) -> str:
        return str(self.tag)
