from tortoise.models import Model
from tortoise import fields


class Reservation(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField('models.User', related_name='reservations', on_delete=fields.CASCADE)
    minister = fields.ForeignKeyField('models.Minister', related_name='reservations', on_delete=fields.CASCADE)
    minister_type = fields.ForeignKeyField('models.MinisterType', related_name='reservations', on_delete=fields.CASCADE)
    alliance = fields.ForeignKeyField('models.Alliance', related_name='reservations', on_delete=fields.CASCADE)
    state = fields.ForeignKeyField('models.State', related_name="reservations", on_delete=fields.CASCADE)
    schedule_date = fields.DateField(null=False)
    schedule_time = fields.CharField(max_length=5)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "reservations"
        unique_together = (("user", "schedule_date", "schedule_time"),)