from pydantic import BaseModel
from .alliance import AllianceSchema
from .minister import MinisterSchema
from .user import UserSchema
from .schedule import ScheduleSchema
from .state import StateSchema


class ReservationSchema(BaseModel):
    user: UserSchema
    state: StateSchema
    alliance: AllianceSchema
    schedule: ScheduleSchema
    minister: MinisterSchema
