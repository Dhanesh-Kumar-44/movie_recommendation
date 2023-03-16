# , cache, login_manager
# from main import db, app
from models.db import db
from savalidation import ValidationMixin
from datetime import datetime

class BaseModel(db.Model, ValidationMixin):
    __abstract__ = True

    created_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(BaseModel, self).__init__(**kwargs)
        if not self.created_on:
            self.created_on = datetime.utcnow()
        self.updated_on = datetime.utcnow()