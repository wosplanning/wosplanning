from tortoise.models import Model
from tortoise import fields


class State(Model):
    id = fields.IntField(primary_key=True)

    alliances = fields.ManyToManyField(
        "models.Alliance",
        related_name="states",
        on_delete = fields.CASCADE
    )

    class Meta:
        table = "states"

    def __str__(self) -> str:
        return str(self.id)
