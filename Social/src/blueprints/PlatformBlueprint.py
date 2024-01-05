from flask import request, Blueprint, make_response
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from flask_jwt_extended import jwt_required, get_jwt_identity
from Social.src.utils.helpers import role_required
from Social.src.utils.models import db, States, PlatformUsers, Posts, Comments, Platforms, Pages
from sqlalchemy.sql import func, extract, distinct
import json
import traceback
import logging as log
import pandas as pd

platform_app = Blueprint('platform_app', __name__)


@platform_app.route('/get_platform_details', methods=['GET', 'POST'])
@jwt_required()
@role_required(['Admin'])
def get_platform_details():
    """
        Route method for getting platform details.
        input - JSON {key:'', value: ''}
    """
    try:
        if request.method == 'GET':
            state = request.args.get('state', None)
            time_slice = request.args.get('time_slice', '')
        else:
            params = request.get_json()
            state = params.get('state', None)
            time_slice = params.get('time_slice', '')

        # session_user = get_jwt_identity()
        res_data = {
            "data": [
                {
                    "icon": "cibFacebook",
                    "values": [],
                    "capBg": {
                        "--cui-card-cap-bg": "#3b5998"
                    },
                    "color": "primary"
                },
                {
                    "icon": "cibTwitter",
                    "values": [{"title": "Users", "value": "0"}, {"title": "tweets", "value": "0"}],
                    "capBg": {
                        "--cui-card-cap-bg": "#00aced"
                    },
                    "color": "info"
                },
                {
                    "icon": "cibInstagram",
                    "values": [{"title": "Users", "value": "0"}, {"title": "Posts", "value": "0"}],
                    "capBg": {
                        "--cui-card-cap-bg": "#00bced"
                    },
                    "color": "warning"
                }
            ]
        }

        if state is None or len(state) == 0:
            platforms_records = db.session.query(func.count(PlatformUsers.email_id).label("count"),
                                                 PlatformUsers.platform_name).group_by(
                PlatformUsers.platform_name).all()
        else:
            platforms_records = db.session.query(func.count(PlatformUsers.email_id).label("count"),
                                                 PlatformUsers.platform_name).where(
                func.trim(func.lower(PlatformUsers.state_code)) == state.lower()).group_by(
                PlatformUsers.platform_name).all()

        if len(platforms_records) > 0:
            _fields = platforms_records[0]._fields
        else:
            _fields = ["count", "platform_name"]

        _recs = [{your_key: getattr(x, your_key) for your_key in _fields} for x in platforms_records]

        tweets_records = db.session.query(Platforms.platform_name,
                                          func.count(Posts.post_id).label("count")).where(
            Posts.page_id == Pages.page_id, Pages.platform_name == Platforms.platform_name).group_by(
            Platforms.platform_name).all()
        tweets_recs = [{your_key: getattr(x, your_key) for your_key in tweets_records[0]._fields} for x in
                       tweets_records]

        for i in _recs:
            if i.get("platform_name").lower().startswith("facebook"):
                res_data["data"][0]["values"] = []
                res_data["data"][0]["values"].append({"title": "Users", "value": i.get("count")})

                _flag = True
                for x in tweets_recs:
                    if x.get("platform_name").lower().startswith("facebook"):
                        _flag = False
                        res_data["data"][0]["values"].append(
                            {"title": "Posts", "value": str(x.get("count"))})
                if _flag:
                    res_data["data"][0]["values"].append({"title": "Posts", "value": "0"})
            elif i.get("platform_name").lower().startswith("twitter"):
                res_data["data"][1]["values"] = []
                res_data["data"][1]["values"].append({"title": "Users", "value": i.get("count")})

                _flag = True
                for x in tweets_recs:
                    if x.get("platform_name").lower().startswith("twitter"):
                        _flag = False
                        res_data["data"][1]["values"].append(
                            {"title": "Tweets", "value": str(x.get("count"))})
                if _flag:
                    res_data["data"][1]["values"].append({"title": "Tweets", "value": "0"})
            elif i.get("platform_name").lower().startswith("instagram"):
                res_data["data"][2]["values"] = []
                res_data["data"][2]["values"].append({"title": "Users", "value": i.get("count")})

                _flag = True
                for x in tweets_recs:
                    if x.get("platform_name").lower().startswith("instagram"):
                        _flag = False
                        res_data["data"][2]["values"].append(
                            {"title": "Posts", "value": str(x.get("count"))})
                if _flag:
                    res_data["data"][2]["values"].append({"title": "Posts", "value": "0"})

        return json.dumps(Response(status=True, message="Platform records retrieved.", data=res_data).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch platform details.", data={}).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)


@platform_app.route('/get_comments', methods=['GET', 'POST'])
@jwt_required()
@role_required(['Admin'])
def get_comments():
    """
        Route method for getting user details.
        input - JSON {key:'', value: ''}
    """
    try:
        if request.method == 'GET':
            email_id = request.args.get('email_id', None)
        else:
            params = request.get_json()
            email_id = params.get('email_id', None)

        # session_user = get_jwt_identity()
        if email_id is not None:
            docs = db.session.query(Comments.comment_url, Comments.comment_id, Comments.email_id,
                                    Comments.comment_content,
                                    Comments.classification, Comments.score, Comments.user).where(
                PlatformUsers.email_id == email_id).all()
        else:
            docs = db.session.query(Comments.comment_url, Comments.comment_id, Comments.email_id,
                                    Comments.comment_content,
                                    Comments.classification, Comments.score, Comments.user).all()

        if len(docs) > 0:
            _fields = docs[0]._fields
        else:
            _fields = ["comment_url", "comment_id", "email_id", "comment_content", "classification", "score", "user"]

        _recs = [{your_key: getattr(x, your_key) for your_key in _fields} for x in docs]
        return json.dumps(Response(status=True, message="Comments retrieved.", data=_recs).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch comments.", data={}).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)


@platform_app.route('/get_users', methods=['GET', 'POST'])
@jwt_required()
@role_required(['Admin'])
def get_users():
    """
        Route method for getting user details.
        input - JSON {key:'', value: ''}
    """
    try:
        if request.method == 'GET':
            state = request.args.get('state', None)
            return_as = request.args.get('return_as', 'json')
        else:
            params = request.get_json()
            state = params.get('state', None)
            return_as = request.args.get('return_as', 'json')

        # session_user = get_jwt_identity()
        if state is not None and len(state) > 0:
            docs = db.session.query(PlatformUsers.email_id, PlatformUsers.state_code, PlatformUsers.profile_img,
                                    PlatformUsers.platform_name, PlatformUsers.behaviour_type, PlatformUsers.score,
                                    PlatformUsers.contact, PlatformUsers.first_name, Platforms.icon).where(
                func.trim(func.lower(PlatformUsers.state_code)) == state.lower(),
                PlatformUsers.platform_name == Platforms.platform_name).all()
        else:
            docs = db.session.query(PlatformUsers.email_id, PlatformUsers.state_code, PlatformUsers.profile_img,
                                    PlatformUsers.platform_name, PlatformUsers.behaviour_type, PlatformUsers.score,
                                    PlatformUsers.contact, PlatformUsers.first_name, Platforms.icon).where(
                PlatformUsers.platform_name == Platforms.platform_name).all()

        if len(docs) > 0:
            _fields = docs[0]._fields
        else:
            _fields = ["email_id", "state_code", "profile_img", "platform_name", "behaviour_type", "score", "contact",
                       "first_name", "icon"]

        _recs = [{your_key: getattr(x, your_key) for your_key in _fields} for x in docs]

        if return_as.lower().strip() == 'csv':
            resp = make_response(pd.DataFrame(_recs).to_csv(
                columns=["email_id", "state_code", "platform_name", "behaviour_type", "score", "contact", "first_name"],
                index=False, sep=",", quotechar='"', encoding="utf-8"))
            resp.headers["Content-Disposition"] = "attachment; filename=users.csv"
            resp.headers["Content-Type"] = "text/csv"
            return resp
        else:
            return json.dumps(Response(status=True, message="Users retrieved.", data=_recs).__dict__,
                              cls=CustomJSONEncoder, ensure_ascii=False)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to user list.", data={}).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)


@platform_app.route('/get_user_profile', methods=['GET', 'POST'])
@jwt_required()
@role_required(['Admin'])
def get_user_profile():
    """
        Route method for getting user details.
        input - JSON {key:'', value: ''}
    """
    try:
        if request.method == 'GET':
            email_id = request.args.get('email_id', None)
            platform_name = request.args.get('platform_name', None)
        else:
            params = request.get_json()
            email_id = params.get('email_id', None)
            platform_name = params.get("platform_name", None)

        # session_user = get_jwt_identity()

        if email_id is None or len(email_id) == 0 or platform_name is None:
            return json.dumps(Response(status=False, message="Missing userid/platform details.", data={}).__dict__,
                              cls=CustomJSONEncoder, ensure_ascii=False)

        docs = db.session.query(PlatformUsers.email_id, PlatformUsers.state_code, PlatformUsers.profile_img,
                                PlatformUsers.platform_name, PlatformUsers.behaviour_type, PlatformUsers.score,
                                PlatformUsers.contact, PlatformUsers.first_name, PlatformUsers.middle_name,
                                PlatformUsers.last_name, PlatformUsers.dob, PlatformUsers.profile_url).where(
            func.trim(func.lower(PlatformUsers.email_id)) == email_id.lower(),
            func.trim(func.lower(PlatformUsers.platform_name)) == platform_name.lower()).all()

        if len(docs) > 0:
            _fields = docs[0]._fields
        else:
            _fields = ["email_id", "state_code", "profile_img", "platform_name", "behaviour_type", "score", "contact",
                       "first_name", "middle_name", "last_name", "dob", "profile_url"]

        _recs = [{your_key: getattr(x, your_key) for your_key in _fields} for x in docs]

        _cdocs = db.session.query(Comments.comment_url, Comments.comment_id, Comments.email_id,
                                  Comments.comment_content,
                                  Comments.classification, Comments.score, Comments.user, Comments.post_id,
                                  Posts.post_content).where(Comments.email_id == email_id,
                                                            Comments.post_id == Posts.post_id).all()

        if len(_cdocs) > 0:
            _cfields = _cdocs[0]._fields
        else:
            _cfields = ["comment_url", "comment_id", "email_id", "comment_content", "classification", "score", "user",
                        "post_id", "post_content"]

        _crecs = [{your_key: getattr(x, your_key) for your_key in _cfields} for x in _cdocs]
        _recs[0]["comments"] = _crecs
        return json.dumps(Response(status=True, message="User profile retrieved.", data=_recs).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch user profile.", data={}).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)


@platform_app.route('/get_post_details', methods=['GET', 'POST'])
@jwt_required()
@role_required(['Admin'])
def get_post_details():
    """
        Route method for getting user details.
        input - JSON {key:'', value: ''}
    """
    try:
        if request.method == 'GET':
            post_id = request.args.get('id', None)
        else:
            params = request.get_json()
            post_id = params.get('id', None)

        # session_user = get_jwt_identity()
        if post_id is None and len(post_id) == 0:
            return json.dumps(Response(status=False, message="Unable to get post details.", data={}).__dict__,
                              cls=CustomJSONEncoder, ensure_ascii=False)
        else:
            docs = db.session.query(Comments.comment_content, Comments.user,
                                    Comments.score, Comments.classification, Comments.email_id,
                                    Comments.created_on).where(Comments.post_id == post_id).limit(50).all()

        if len(docs) > 0:
            _fields = docs[0]._fields
        else:
            _fields = ["post_id", "post_content", "comment_content", "user", "score", "classification", "email_id",
                       "created_on"]

        _recs = [{your_key: getattr(x, your_key) for your_key in _fields} for x in docs]

        return json.dumps(Response(status=True, message="Post data retrieved.", data=_recs).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to user list.", data={}).__dict__,
                          cls=CustomJSONEncoder, ensure_ascii=False)
