from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(primary_key=True)
    username = fields.CharField(max_length=16)
    state = fields.ForeignKeyField('models.State', related_name='users', null=False, on_delete=fields.CASCADE)
    alliance = fields.ForeignKeyField('models.Alliance', related_name='users', null=True, on_delete=fields.CASCADE)

    class Meta:
        table = "users"

    def __str__(self) -> str:
        return str(self.username)
