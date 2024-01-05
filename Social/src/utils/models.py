from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256
from Social.src.configurations.settings import DB_SCHEMA
from sqlalchemy import MetaData

metadata = MetaData(
    naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

db = SQLAlchemy(metadata=metadata)

class Audit(db.Model):
    __tablename__ = "audit"
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    timestamp = db.Column(db.DateTime)
    user = db.Column(db.String)
    client_ip = db.Column(db.String)
    status = db.Column(db.String)
    task_id = db.Column(db.String)
    request_uri = db.Column(db.String)
    result = db.Column(db.String)
    application = db.Column(db.String)
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    request_body = db.Column(db.JSON)

    def __repr__(self):
        return "<Audit Entry: {} with status {}>".format(self.id, self.status)

    def __init__(self, user, client_ip, status, result, task_id, request_uri, application, request_body={}):
        self.user = user
        self.client_ip = client_ip
        self.status = status
        self.task_id = task_id
        self.result = result
        self.request_uri = request_uri
        self.timestamp = datetime.now()
        self.application = application
        self.month = datetime.now().month
        self.year = datetime.now().year
        self.request_body = request_body


class User(db.Model):
    __tablename__ = "user"
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    email_id = db.Column(db.String, nullable=False, unique=True, primary_key=True)
    first_name = db.Column(db.String, nullable=False, server_default='')
    last_name = db.Column(db.String, nullable=False, server_default='')
    created_by = db.Column(db.String, nullable=False, server_default='')
    created_on = db.Column(db.DateTime, nullable=False)
    updated_by = db.Column(db.String, nullable=True, server_default='')
    updated_on = db.Column(db.DateTime, nullable=True)
    password = db.Column(db.String, nullable=False, server_default='')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role = db.Column(db.Text, nullable=False, server_default='user')
    last_login = db.Column(db.DateTime, nullable=True)
    force_pwd_change = db.Column(db.Boolean, default=True, nullable=True)
    lang = db.Column(db.String())

    def __init__(self, email_id, first_name, last_name, created_by, is_active, role, password="", last_login=None,
                 force_pwd_change=True, lang="en"):
        self.email_id = email_id
        self.first_name = first_name
        self.last_name = last_name
        self.created_by = created_by
        self.is_active = is_active
        self.role = role
        self.password = password
        self.created_on = datetime.now()
        self.last_login = last_login
        self.force_pwd_change = force_pwd_change
        self.lang = lang

    def __repr__(self):
        return self.username

    @classmethod
    def get_user_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def verify_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)

    def set_password(self, password):
        self.password = pbkdf2_sha256.hash(password)

    def delete_tokens(self):
        self.tokens.delete()

    def to_dict(self):
        return dict(
            id=self.id,
            first_name=self.first_name,
        )


class Platforms(db.Model):
    __tablename__ = 'platforms'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    platform_name = db.Column(db.String, primary_key=True)
    description = db.Column(db.String)
    icon = db.Column(db.String)
    card_color = db.Column(db.String)

    def __init__(self, platform_name, description, icon, card_color):
        self.platform_name = platform_name
        self.description = description
        self.icon = icon
        self.card_color = card_color


class Pages(db.Model):
    __tablename__ = 'pages'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    page_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    if DB_SCHEMA is not None:
        platform_name = db.Column(db.String, db.ForeignKey(DB_SCHEMA + '.platforms.platform_name'))
        politician_id = db.Column(db.Integer, db.ForeignKey(DB_SCHEMA + '.politicians.politician_id'))
    else:
        platform_name = db.Column(db.String, db.ForeignKey('platforms.platform_name'))
        politician_id = db.Column(db.Integer, db.ForeignKey('politicians.politician_id'))

    page_name = db.Column(db.String)
    page_url = db.Column(db.String)
    description = db.Column(db.String)
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)

    def __init__(self, page_name, page_url, platform_name, politician_id, description, created_by):
        self.page_name = page_name
        self.page_url = page_url
        self.platform_name = platform_name
        self.politician_id = politician_id
        self.description = description
        self.created_on = datetime.now()
        self.created_by = created_by


class Posts(db.Model):
    __tablename__ = 'posts'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    post_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    if DB_SCHEMA is not None:
        page_id = db.Column(db.Integer, db.ForeignKey(DB_SCHEMA + '.pages.page_id'))
    else:
        page_id = db.Column(db.Integer, db.ForeignKey('pages.page_id'))
    post_content = db.Column(db.String)
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)
    classification = db.Column(db.String)
    score = db.Column(db.Integer)

    def __init__(self, page_id, post_content, created_by, score=0.0, classification=""):
        self.page_id = page_id
        self.post_content = post_content
        self.created_on = datetime.now()
        self.created_by = created_by
        self.score = score
        self.classification = classification


class Comments(db.Model):
    __tablename__ = 'comments'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    if DB_SCHEMA is not None:
        post_id = db.Column(db.Integer, db.ForeignKey(DB_SCHEMA + '.posts.post_id'))
        email_id = db.Column(db.String, db.ForeignKey(DB_SCHEMA + 'platform_users.email_id'))
    else:
        post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'))
        email_id = db.Column(db.String, db.ForeignKey('platform_users.email_id'))
    comment_content = db.Column(db.String)
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)
    user = db.Column(db.String)
    classification = db.Column(db.String)
    score = db.Column(db.Integer)
    comment_url = db.Column(db.String)

    def __init__(self, comment_content, post_id, email_id, user, classification, score, comment_url, created_by):
        self.comment_content = comment_content
        self.post_id = post_id
        self.user = user
        self.email_id = email_id
        self.classification = classification
        self.score = score
        self.comment_url = comment_url
        self.created_on = datetime.now()
        self.created_by = created_by


class Country(db.Model):
    __tablename__ = 'country'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    country_name = db.Column(db.String, primary_key=True)
    description = db.Column(db.String)

    def __init__(self, country_name, description=""):
        self.country_name = country_name
        self.description = description


class States(db.Model):
    __tablename__ = 'states'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    state_code = db.Column(db.String, primary_key=True)
    if DB_SCHEMA is not None:
        country_name = db.Column(db.String, db.ForeignKey(DB_SCHEMA + '.country.country_name'))
    else:
        country_name = db.Column(db.String, db.ForeignKey('country.country_name'))
    state_name = db.Column(db.String)
    description = db.Column(db.String)
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)
    lat = db.Column(db.Integer)
    long = db.Column(db.Integer)
    rs_seats = db.Column(db.Integer)
    ls_seats = db.Column(db.Integer)

    def __init__(self, state_name, state_code, country_name, description, lat, long, created_by):
        self.state_name = state_name
        self.state_code = state_code
        self.country_name = country_name
        self.description = description
        self.created_on = datetime.now()
        self.created_by = created_by
        self.lat = lat
        self.long = long


class PlatformUsers(db.Model):
    __tablename__ = 'platform_users'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    email_id = db.Column(db.String, primary_key=True)
    if DB_SCHEMA is not None:
        platform_name = db.Column(db.String, db.ForeignKey(DB_SCHEMA + '.platforms.platform_name'))
    else:
        platform_name = db.Column(db.String, db.ForeignKey('platforms.platform_name'))
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    middle_name = db.Column(db.String)
    contact = db.Column(db.String)
    dob = db.Column(db.String)
    profile_img = db.Column(db.String)
    if DB_SCHEMA is not None:
        state_code = db.Column(db.String, db.ForeignKey(DB_SCHEMA + '.states.state_code'))
    else:
        state_code = db.Column(db.String, db.ForeignKey('states.state_code'))
    behaviour_type = db.Column(db.String)
    profile_url = db.Column(db.String)
    score = db.Column(db.Integer)
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)

    def __init__(self, email_id, platform_name, first_name, last_name, middle_name, contact, dob, profile_img,
                 state_code, created_by, behaviour_type, score=0.0):
        self.email_id = email_id
        self.platform_name = platform_name
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.contact = contact
        self.dob = dob
        self.profile_img = profile_img
        self.state_code = state_code
        self.created_on = datetime.now()
        self.created_by = created_by
        self.behaviour_type = behaviour_type
        self.score = score


class Parties(db.Model):
    __tablename__ = 'parties'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    party_code = db.Column(db.String, primary_key=True)
    party_name = db.Column(db.String)
    party_type = db.Column(db.String)
    party_region = db.Column(db.String)
    color = db.Column(db.String)
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)

    def __init__(self, party_code, party_name, party_type, party_region, color, created_by):
        self.party_code = party_code
        self.party_name = party_name
        self.party_type = party_type
        self.party_type = party_type
        self.party_region = party_region
        self.color = color
        self.created_on = datetime.now()
        self.created_by = created_by


class PartyInPower(db.Model):
    __tablename__ = 'party_in_power'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    map_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.Boolean)
    if DB_SCHEMA is not None:
        state_code = db.Column(db.String, db.ForeignKey(DB_SCHEMA + '.states.state_code'))
        party_code = db.Column(db.String, db.ForeignKey(DB_SCHEMA + '.parties.party_code'))
    else:
        state_code = db.Column(db.String, db.ForeignKey('states.state_code'))
        party_code = db.Column(db.String, db.ForeignKey('parties.party_code'))
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)

    def __init__(self, state_code, party_code, created_by, status=True):
        self.state_code = state_code
        self.party_code = party_code
        self.status = status
        self.created_on = datetime.now()
        self.created_by = created_by


class Politicians(db.Model):
    __tablename__ = 'politicians'
    if DB_SCHEMA is not None:
        __table_args__ = {'schema': DB_SCHEMA}
    politician_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    if DB_SCHEMA is not None:
        party_code = db.Column(db.String, db.ForeignKey(DB_SCHEMA + '.parties.party_code'))
        state_code = db.Column(db.String, db.ForeignKey(DB_SCHEMA + 'states.state_code'))
    else:
        party_code = db.Column(db.String, db.ForeignKey('parties.party_code'))
        state_code = db.Column(db.String, db.ForeignKey('states.state_code'))
    politician_name = db.Column(db.String)
    politician_img_url = db.Column(db.String)
    description = db.Column(db.String)
    designation = db.Column(db.String)
    score = db.Column(db.Integer)
    activeness_group = db.Column(db.String)
    created_on = db.Column(db.DateTime)
    created_by = db.Column(db.String)

    def __init__(self, politician_name, politician_img_url, party_code, state_code, description, designation, created_by, score=0.0, activeness_group=""):
        self.politician_name = politician_name
        self.politician_img_url = politician_img_url
        self.party_code = party_code
        self.state_code = state_code
        self.description = description
        self.designation = designation
        self.created_on = datetime.now()
        self.created_by = created_by
        self.score = score
        self.activeness_group = activeness_group
