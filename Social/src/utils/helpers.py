from Social.src.configurations.settings import CIPHER_SUITE
from Social.src.utils.models import db, User, States, Parties, PartyInPower, Pages, Posts, Comments, PlatformUsers
from Social.src.configurations.settings import ALLOWED_EXTENSIONS
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
import logging as log
import traceback

ROLE_ERROR = "Unauthorized Access, Admins only"


def role_required(access_level):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            role_access = get_jwt()
            type = db.session.query(User.role).filter(User.email_id == role_access['sub']).first()
            if isinstance(access_level, list):
                if type is None:
                    return jsonify(message=ROLE_ERROR), 403

                if type[0] not in access_level:
                    return jsonify(message=ROLE_ERROR), 403
            else:
                if not type[0] == access_level:
                    return jsonify(message=ROLE_ERROR), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


def encrypt(message):
    return CIPHER_SUITE.encrypt(str.encode(message))


def decrypt(token):
    return CIPHER_SUITE.decrypt(token).decode('utf-8')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_icon(tf, icon_map):
    try:
        if tf in list(icon_map.keys()):
            return icon_map[tf]
        else:
            return ""
    except Exception as ex:
        log.error(ex)
        log.error(traceback.print_exc())


def bootstrap_data():
    try:
        log.info("Bootstrapping Data.")
        records = db.session.query(User.first_name, User.last_name, User.email_id, User.is_active, User.role).all()

        if len(records) > 0:
            log.info("Bootstrapping Not Required.")
            return True
        else:
            required_dict = {
                "first_name": "AICC-Admin",
                "last_name": "AICC",
                "password": "AICC@1231",
                "email": "varun@aisalanalytics.com",
                "role": "Admin"
            }

            user_entry = User(first_name=required_dict["first_name"], last_name=required_dict["last_name"],
                              password="", email_id=required_dict["email"], is_active=True, role=required_dict["role"], created_by=required_dict["email"])
            user_entry.set_password(required_dict["password"])
            db.session.add(user_entry)

            required_dict = {
                "first_name": "AISAL",
                "last_name": "AISAL",
                "password": "aisal",
                "email": "aisal",
                "role": "Admin"
            }

            user_entry = User(first_name=required_dict["first_name"], last_name=required_dict["last_name"],
                              password="", email_id=required_dict["email"], is_active=True, role=required_dict["role"], created_by=required_dict["email"])
            user_entry.set_password(required_dict["password"])
            db.session.add(user_entry)

            db.session.commit()

            import pandas as pd
            df = pd.read_csv("D:\AISAL\Data\States.csv", sep=',', quotechar='"')
            df.fillna("", inplace=True)
            recs = df.to_dict("records")
            for i in recs:
                _entry = States(country_name=i.get("country_name"), state_code=i.get("state_name"),
                                state_name=i.get("state_name"), description=i.get("description"), lat=i.get("lat"),
                                long=i.get("long"), created_by=i.get("created_by"))
                db.session.add(_entry)

            db.session.commit()

            df = pd.read_csv("D:\AISAL\Data\Parties.csv", sep=',', quotechar='"')
            df.fillna("", inplace=True)
            recs = df.to_dict("records")
            for i in recs:
                _entry = Parties(party_code=i.get("party_code"), party_name=i.get("party_name"),
                                 party_type=i.get("party_type"), party_region=i.get("party_region"),
                                 color=i.get("color"),
                                 created_by=i.get("created_by"))
                db.session.add(_entry)

            db.session.commit()

            df = pd.read_csv("D:\AISAL\Data\parties_in_power.csv", sep=',', quotechar='"')
            df.fillna("", inplace=True)
            recs = df.to_dict("records")
            for i in recs:
                _entry = PartyInPower(state_code=i.get("state_code"), party_code=i.get("party_code"),
                                      created_by=i.get("created_by"))
                db.session.add(_entry)

            db.session.commit()

            page_required_dict = {
                "page_name": "Facebook Public",
                "description": "Public pages for scrapping FB data.",
                "created_by": "Admin"
            }
            page_entry = Pages(page_name=page_required_dict["page_name"], description=page_required_dict["description"],
                               created_by=page_required_dict["created_by"])
            db.session.add(page_entry)

            db.session.commit()
            print(page_entry.page_id)

            df = pd.read_csv("D:\AISAL\Data\platform_users.csv", sep=',', quotechar='"')
            df.fillna("", inplace=True)
            recs = df.to_dict("records")
            for i in recs:
                _entry = PlatformUsers(email_id=i.get("email_id"), platform_name=i.get("platform_name"),
                                       first_name=i.get("first_name"), last_name=i.get("last_name"),
                                       middle_name=i.get("middle_name"), contact=i.get("contact"),
                                       dob=i.get("dob"), profile_img=i.get("profile_img"),
                                       state_code=i.get("state_code"), behaviour_type=i.get("behaviour_type"),
                                       score=i.get("score"), created_by=i.get("created_by"))
                db.session.add(_entry)

            db.session.commit()

            df = pd.read_csv("D:\AISAL\Data\Posts.csv", sep=',', quotechar='"')
            df.fillna("", inplace=True)
            recs = df.to_dict("records")
            for i in recs:
                _entry = Posts(page_id=i.get("page_id"), post_content=i.get("post_content"), created_by=i.get("created_by"))
                db.session.add(_entry)

            db.session.commit()

            df = pd.read_csv("D:\AISAL\Data\comments.csv", sep=',', quotechar='"')
            df.fillna("", inplace=True)
            recs = df.to_dict("records")
            for i in recs:
                _entry = Comments(comment_content=i.get("comment_content"), post_id=i.get("post_id"),
                                  email_id=i.get("email_id"), user=i.get("user"),
                                  classification=i.get("classification"), score=i.get("score"),
                                  comment_url=i.get("comment_url"), created_by=i.get("created_by"))
                db.session.add(_entry)

            db.session.commit()

            log.info("Bootstrapping Done.")
            return True
    except Exception as ex:
        log.error(traceback.print_exc())
        return False
