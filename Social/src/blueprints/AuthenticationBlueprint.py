from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from Social.src.utils.models import Audit, db, User
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from Social.src.configurations.settings import TOKEN_EXPIRY, PWD_EXPIRE_DAYS
import ast
import datetime
import logging as log
import traceback
import json

auth_app = Blueprint('auth_app', __name__)


@auth_app.route('/auth', methods=['POST'])
def do_admin_login():
    try:
        params = request.get_json()
        user_password = params.get('password', None)
        user_name = params.get('username', None)
        client_token = params.get("client_token", None)
        fail_counter = int(params.get('failCounter', 0))

        if client_token is not None:
            client_token = client_token.encode("utf-8")

        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip = request.remote_addr

        # user_db = db.session.query(User.email_id, User.updated_on, User.created_on, User.force_pwd_change, User.role,
        #                            User.last_login).where(User.email_id == user_name, User.is_active == True).one()
        user_db = User.query.filter(User.email_id == user_name, User.is_active == True).first()
        updated_on = None
        force_pwd_change = None
        try:
            if user_db and not user_db.email_id.isspace():
                if user_db.verify_password(user_password):
                    if user_db.updated_on:
                        updated_on = user_db.updated_on
                    else:
                        updated_on = user_db.created_on

                    if int((datetime.datetime.now() - updated_on).days) > PWD_EXPIRE_DAYS:
                        user_db.force_pwd_change = True
                        force_pwd_change = True
                    else:
                        force_pwd_change = user_db.force_pwd_change

                    db.session.query(User).filter(User.email_id == user_name, User.is_active == True).update(
                        {"last_login": datetime.datetime.now()})

                    expires = datetime.timedelta(minutes=TOKEN_EXPIRY)
                    access_token = create_access_token(identity=user_name, expires_delta=expires)
                    log_entry = Audit(
                        user=user_db.email_id,
                        client_ip=ip,
                        status="SUCCESS",
                        task_id="",
                        request_uri=request.path,
                        result="Token Provided",
                        application="AUTH"
                    )

                    db.session.add(log_entry)
                    db.session.commit()
                    log.info("Token assigned to user - {0}".format(user_db.email_id))
                    return json.dumps(Response(status=True, message="Token Assigned.",
                                               data={"username": user_db.email_id, "token": access_token,
                                                     "role": user_db.role, "last_login": user_db.last_login,
                                                     "force_pwd_change": force_pwd_change}).__dict__,
                                      cls=CustomJSONEncoder)
                else:
                    log_entry = Audit(
                        user=user_db.email_id,
                        client_ip=ip,
                        status="ERROR",
                        task_id="",
                        request_uri=request.path,
                        result="Token Denied",
                        application='AUTH'
                    )

                    db.session.add(log_entry)

                    if int(fail_counter) > 5:
                        db.session.query(User).filter(User.email_id == user_db.email_id).update({"is_active": False})
                        log.info("Inactive Marked for user - {0}".format(user_db.email_id))

                        disable_log_entry = Audit(
                            user=user_db.email_id,
                            client_ip=str(request.remote_addr),
                            status="SUCCESS",
                            result="DISABLED USER",
                            task_id="",
                            request_uri=str(request.path),
                            application="USER"
                        )
                        db.session.add(disable_log_entry)
                        db.session.commit()
                        return json.dumps(Response(status=False, message="User locked after multiple failed attempts.",
                                                   data={}).__dict__, cls=CustomJSONEncoder)

                    db.session.commit()
                    return json.dumps(Response(status=False, message="Invalid Credentials.", data={}).__dict__, cls=CustomJSONEncoder)
            else:
                log_entry = Audit(
                    user=str(user_name),
                    client_ip=ip,
                    status="ERROR",
                    task_id="",
                    request_uri=request.path,
                    result="Token Denied",
                    application='AUTH'
                )

                db.session.add(log_entry)
                db.session.commit()
                return json.dumps(Response(status=False, message="Username not found in database.", data={}).__dict__, cls=CustomJSONEncoder)
        except Exception as ex:
            log.error(str(ex))
            log.error(traceback.print_exc())
            return json.dumps(Response(status=False, message="Exception found, please contact administrator.", data={}).__dict__,
                              cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        print(traceback.print_exc())
        return json.dumps(Response(status=False, message="Invalid Credentials.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@auth_app.route("/refresh", methods=["POST"])
@jwt_required()
def refresh():
    identity = get_jwt_identity()

    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr

    expires = datetime.timedelta(minutes=TOKEN_EXPIRY)
    access_token = create_access_token(identity=identity, expires_delta=expires)
    log_entry = Audit(
        user=identity,
        client_ip=ip,
        status="SUCCESS",
        task_id="",
        request_uri=request.path,
        result="Token Refreshed",
        application="AUTH"
    )

    db.session.add(log_entry)
    db.session.commit()
    log.info("Token assigned to user - {0}".format(identity))
    return json.dumps(Response(status=True, message="Token Refreshed.", data={"token": access_token}).__dict__,
                      cls=CustomJSONEncoder)
