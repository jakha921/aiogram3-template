from aiogram.fsm.state import StatesGroup, State


class GetPhone(StatesGroup):
    phone = State()


class AdminInvoicesFilter(StatesGroup):
    year = State()
    month = State()
    invoices_list = State()
    invoice_details = State()
