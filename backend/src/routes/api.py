from typing import Optional
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from ..models import apply_filters, AllianceModel, \
    StateModel, MinisterModel, MinisterTypeModel, \
    UserModel, ReservationModel
from ..schemas.reservation import ReservationSchema
from tortoise.exceptions import OperationalError
from tortoise.transactions import in_transaction


api = APIRouter(prefix="/api")


@api.get("/alliances")
async def api_get_alliances(
    alliance_id: Optional[int] = Query(None),
    alliance_tag: Optional[str] = Query(None),
):
    alliances = await AllianceModel.filter(
        **apply_filters({
            "id": alliance_id,
            "tag": alliance_tag,
        })
    ).order_by("id").prefetch_related("states")

    return [
        {
            "id": alliance.id,
            "tag": alliance.tag,
            "states": [alliance for alliance in alliance.states],
        } for alliance in alliances
    ]


@api.get("/states")
async def api_get_states(state_id: Optional[int] = Query(None)):
    states = await StateModel.filter(
        **apply_filters({
            "id": state_id,
        })
    ).order_by("id").prefetch_related("alliances")

    return [
        {
            "id": state.id,
            "alliances": [alliance for alliance in state.alliances],
        } for state in states
    ]


@api.get("/ministers")
async def api_get_ministers(minister_id: Optional[int] = Query(None)):
    ministers = await MinisterModel.filter(
        **apply_filters({
            "id": minister_id,
        })
    ).order_by("id").prefetch_related("types")

    return [
        {
            "id": minister.id,
            "name": minister.name,
            "types": [minister_type for minister_type in minister.types]
        } for minister in ministers
    ]


@api.get("/users")
async def api_get_users(user_id: Optional[int] = Query(None)):
    users = await UserModel.filter(
        **apply_filters({
            "id": user_id,
        })
    ).order_by("id").prefetch_related("alliance", "state")

    return [
        {
            "id": user.id,
            "nickname": user.username,
            "alliance": user.alliance,
            "state": user.state,
        } for user in users
    ]


@api.get("/users/{user_id}")
async def api_get_user(user_id: int):
    user = await UserModel.filter(
        id=user_id
    ).prefetch_related("alliance", "state").first()

    if user is None:
        return JSONResponse(
            status_code=404,
            content={
                "message": "User not found",
                "user_id": user_id,
            }
        )

    return {
        "id": user.id,
        "username": user.username,
        "state": user.state,
        "alliance": user.alliance,
    }


@api.get("/users/{user_id}/reservations")
async def api_get_user(user_id: int):
    return await ReservationModel.filter(**apply_filters({
        "user__id": user_id,
    })).prefetch_related("minister_type")


@api.get("/reservations")
async def api_get_reservations():
    reservations = await (ReservationModel.all()
                          .order_by("id")
                          .prefetch_related("alliance", "minister", "minister_type", "user", "state",))

    return [
        {
            "id": reservation.id,
            "schedule_date": reservation.schedule_date,
            "schedule_time": reservation.schedule_time,
            "user": reservation.user,
            "minister": reservation.minister,
            "minister_type": reservation.minister_type,
            "alliance": reservation.alliance,
            "state": reservation.state,
            "created_at": reservation.created_at,
        } for reservation in reservations
    ]


@api.post("/reservations", status_code=status.HTTP_201_CREATED)
async def api_post_reservations(data: ReservationSchema):
    try:
        async with in_transaction() as connection:
            state = await StateModel.filter(id=data.state.id).first()

            if not state:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="The state doesn't exists",
                )

            alliance = await AllianceModel.filter(id=data.alliance.id).first()

            try:
                await UserModel(
                    id=data.user.id,
                    username=data.user.username,
                    state=state,
                    alliance=alliance,
                ).save(using_db=connection)
            except OperationalError:
                pass

            user = await UserModel.filter(id=data.user.id).first()
            minister = await MinisterModel.filter(id=data.minister.id).first()
            minister_type = await MinisterTypeModel.filter(id=data.minister.type).first()

            taken = await ReservationModel.filter(
                schedule_date=data.schedule.date,
                schedule_time=data.schedule.time,
                minister=minister,
                minister_type=minister_type,
                state=state,
            )

            if taken:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="The date/tine slot is already taken",
                )

            user.username = data.user.username

            await user.save(using_db=connection)

            reservation = await ReservationModel.create(
                user=user,
                state=state,
                alliance=alliance,
                minister=minister,
                minister_type=minister_type,
                schedule_date=data.schedule.date,
                schedule_time=data.schedule.time,
                using_db=connection,
            )
    except OperationalError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))

    return reservation


@api.get("/svs")
async def api_get_svs():
    return [
        {
            "date": "2025-06-16",
            "type": "Construction Day",
            "minister": 'Vice President',
        },
        {
            "date": "2025-06-17",
            "type": "Research Day",
            "minister": 'Vice President',
        },
        {
            "date": "2025-06-19",
            "type": "Training Day",
            "minister": 'Minister of Education',
        },
    ]
