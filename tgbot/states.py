from aiogram.fsm.state import StatesGroup, State


class GetPhone(StatesGroup):
    phone = State()
