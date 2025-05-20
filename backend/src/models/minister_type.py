from tortoise.models import Model
from tortoise import fields


class MinisterType(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=16)

    class Meta:
        table = "minister_types"

    def __str__(self):
        return f"{self.name} Day"
