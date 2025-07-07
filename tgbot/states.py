from aiogram.fsm.state import StatesGroup, State


class GetPhone(StatesGroup):
    phone = State()


class AdminInvoicesFilter(StatesGroup):
    year = State()
    month = State()
    invoices_list = State()
    invoice_details = State()


class ReconciliationActStates(StatesGroup):
    year = State()
    month = State()
    confirm = State()


class UserReconciliationStates(StatesGroup):
    year = State()
    month = State()


class UserInvoicesStates(StatesGroup):
    year = State()
    month = State()
