from tortoise.models import Model
from tortoise import fields


class Minister(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=16)
    types = fields.ManyToManyField("models.MinisterType", related_name="ministers", on_delete=fields.CASCADE)

    class Meta:
        table = "ministers"

    def __str__(self):
        return self.name
