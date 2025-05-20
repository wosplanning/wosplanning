from .alliance import Alliance as AllianceModel
from .minister import Minister as MinisterModel
from .minister_type import MinisterType as MinisterTypeModel
from .reservation import Reservation as ReservationModel
from .state import State as StateModel
from .user import User as UserModel


def apply_filters(filters: dict) -> dict:
    result = {}

    for key, value in filters.items():
        if not value:
            continue

        result[key] = value

    return result
