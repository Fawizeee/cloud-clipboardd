# Import all the models, so that Base has them before being
# imported by Alembic
from db.models.base import Base  # noqa
from db.models.user import User  # noqa
from db.models.clipboard import ClipboardItem  # noqa
from db.models.device import Device  # noqa
