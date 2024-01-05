from flask import Blueprint, request
from datetime import datetime
from Social.src.utils.models import db, User, Audit
from Social.src.utils.helpers import role_required
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from flask_jwt_extended import jwt_required, get_jwt_identity
from passlib.hash import pbkdf2_sha256
import json
import logging as log
import traceback
import sqlalchemy

user_app = Blueprint('user_app', __name__)
REQUEST_ERROR_MSG = "Error while processing Request."
SQL_INTEGRITY_MSG = "Duplicate record."
REQUEST_PARAM_MSG = "Invalid data provided, please check all fields are provide and they are not empty."


@user_app.route('/list_users', methods=['POST', 'GET'])
@role_required('Admin')
@jwt_required()
def list_users():
    """
        Route method to list all users..
        input - JSON {}
    """
    try:
        records = db.session.query(User.first_name, User.last_name, User.email_id, User.is_active, User.role).all()

        # Prepare Column Names
        if len(records) > 0:
            keys_to_filter = records[0]._fields
        else:
            keys_to_filter = ["first_name", "last_name", "email", "is_active", "role"]

        # Final Data to be sent as Response
        db_records = [{your_key: getattr(x, your_key) for your_key in keys_to_filter} for x in records]

        # Return Required Output
        if records:
            return json.dumps(
                Response(status=True, message="Operation Successful", data={"records": db_records}).__dict__,
                cls=CustomJSONEncoder)
        else:
            return json.dumps(Response(status=False, message="No Users Found.", data={}).__dict__,
                              cls=CustomJSONEncoder)

    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)))


@user_app.route('/add_user', methods=['POST'])
@jwt_required()
@role_required('Admin')
def add_user():
    """
        Route method to add new user.
        input - JSON {first_name: '', last_name: '', password: '', email: '', role: ''}
    """
    try:
        params = request.get_json()
        try:
            required_dict = {
                "first_name": params.get("first_name", None),
                "last_name": params.get("last_name", None),
                "password": params.get("password", None),
                "email": params.get("email", None),
                "role": params.get("role", None)
            }
            if None not in required_dict.values() and "" not in required_dict.values():
                user_entry = User(first_name=required_dict["first_name"], last_name=required_dict["last_name"],
                                  password="", email_id=required_dict["email"], is_active=True, role=required_dict["role"], created_by=required_dict["email"])
                user_entry.set_password(required_dict["password"])
                db.session.add(user_entry)

                log.info("Database entry created for user - {0}".format(params["email"]))
                session_user = get_jwt_identity()
                log_entry = Audit(
                    user=session_user,
                    client_ip=str(request.remote_addr),
                    status="SUCCESS",
                    result="USER CREATED",
                    task_id="",
                    request_uri=str(request.path),
                    application="USER"
                )
                db.session.add(log_entry)
                db.session.commit()
                return json.dumps(Response(status=True, message="New User Added Successfully.", data={}).__dict__,
                                  cls=CustomJSONEncoder)
            else:
                return json.dumps(Response(status=False,
                                           message=REQUEST_PARAM_MSG,
                                           data={}).__dict__, cls=CustomJSONEncoder)
        except sqlalchemy.exc.IntegrityError as ie:
            log.error(str(ie))
            log.error(traceback.print_exc())
            return json.dumps(Response(status=False,
                                       message=SQL_INTEGRITY_MSG,
                                       data={}).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False,
                                   message=REQUEST_ERROR_MSG,
                                   data={}).__dict__, cls=CustomJSONEncoder)
    finally:
        db.session.close_all()


@user_app.route('/remove_user', methods=['POST'])
@role_required('Admin')
@jwt_required()
def remove_user():
    """
        Route method to delete/active user.
        input - JSON {email: ''}
    """
    try:
        params = request.get_json()
        try:
            required_dict = {
                "email": params.get("email", None)
            }

            if None not in required_dict.values() and "" not in required_dict.values():
                db.session.query(User).filter(User.email_id == required_dict.get("email", "")).update({"is_active": False})
                log.info("Inactive Marked for user - {0}".format(required_dict.get("username", "")))

                session_user = get_jwt_identity()
                log_entry = Audit(
                    user=session_user,
                    client_ip=str(request.remote_addr),
                    status="SUCCESS",
                    result="DISABLED USER",
                    task_id="",
                    request_uri=str(request.path),
                    application="USER"
                )
                db.session.add(log_entry)
                db.session.commit()

                return json.dumps(Response(status=True, message="User Disabled Successfully.", data={}).__dict__,
                                  cls=CustomJSONEncoder)
            else:
                return json.dumps(Response(status=False,
                                           message=REQUEST_PARAM_MSG,
                                           data={}).__dict__, cls=CustomJSONEncoder)
        except sqlalchemy.exc.IntegrityError as ie:
            log.error(str(ie))
            log.error(traceback.print_exc())
            return json.dumps(Response(status=False,
                                       message=SQL_INTEGRITY_MSG,
                                       data={}).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False,
                                   message=REQUEST_ERROR_MSG,
                                   data={}).__dict__, cls=CustomJSONEncoder)
    finally:
        db.session.close_all()


@user_app.route('/enable_user', methods=['POST'])
@role_required('Admin')
@jwt_required()
def enable_user():
    """
        Route method to enable disabled user.
        input - JSON {email: ''}
    """
    try:
        params = request.get_json()
        try:
            required_dict = {
                "email": params.get("email", None)
            }

            if None not in required_dict.values() and "" not in required_dict.values():
                db.session.query(User).filter(User.email_id == required_dict.get("email", ""),
                                              User.is_active == False).update({"is_active": True})
                log.info("Active Marked for user - {0}".format(required_dict.get("username", "")))

                session_user = get_jwt_identity()
                log_entry = Audit(
                    user=session_user,
                    client_ip=str(request.remote_addr),
                    status="SUCCESS",
                    result="ENABLED USER",
                    task_id="",
                    request_uri=str(request.path),
                    application="USER"
                )
                db.session.add(log_entry)
                db.session.commit()

                return json.dumps(Response(status=True, message="User Enabled Successfully.", data={}).__dict__,
                                  cls=CustomJSONEncoder)
            else:
                return json.dumps(Response(status=False,
                                           message=REQUEST_PARAM_MSG,
                                           data={}).__dict__, cls=CustomJSONEncoder)
        except sqlalchemy.exc.IntegrityError as ie:
            log.error(str(ie))
            log.error(traceback.print_exc())
            return json.dumps(Response(status=False,
                                       message=SQL_INTEGRITY_MSG,
                                       data={}).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False,
                                   message=REQUEST_ERROR_MSG,
                                   data={}).__dict__, cls=CustomJSONEncoder)
    finally:
        db.session.close_all()


@user_app.route('/reset_password', methods=['POST'])
@role_required('Admin')
@jwt_required()
def reset_user_password():
    """
        Route method to reset password.
        input - JSON {email: '', new_password: ''}
    """
    try:
        params = request.get_json()
        required_dict = {
            "email": params.get("email", None),
            "new_password": params.get("password", None)
        }

        if None not in required_dict.values() and "" not in required_dict.values():

            existing_user = db.session.query(User).filter(User.email_id == required_dict.get("email", ""),
                                                          User.is_active == True).first()

            if existing_user:
                session_user = get_jwt_identity()

                db.session.query(User).filter(User.email_id == required_dict.get("email", "")).update(
                    {"password": pbkdf2_sha256.hash(required_dict.get("new_password", "")), "force_pwd_change": True,
                     "updated_on": datetime.now(), "updated_by": session_user})

                log.info("Password reset for user - {0}".format(required_dict.get("username", "")))

                log_entry = Audit(
                    user=session_user,
                    client_ip=str(request.remote_addr),
                    status="SUCCESS",
                    result="PASSWORD RESET",
                    task_id="",
                    request_uri=str(request.path),
                    application="USER"
                )
                db.session.add(log_entry)
                db.session.commit()

                return json.dumps(Response(status=True, message="Password Reset Successfully.", data={}).__dict__,
                                  cls=CustomJSONEncoder)
            else:
                return json.dumps(Response(status=False,
                                           message="User is Disabled",
                                           data={}).__dict__, cls=CustomJSONEncoder)
        else:
            return json.dumps(Response(status=False,
                                       message=REQUEST_PARAM_MSG,
                                       data={}).__dict__, cls=CustomJSONEncoder)
    except sqlalchemy.exc.IntegrityError as ie:
        log.error(str(ie))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False,
                                   message=SQL_INTEGRITY_MSG,
                                   data={}).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False,
                                   message=REQUEST_ERROR_MSG,
                                   data={}).__dict__, cls=CustomJSONEncoder)
    finally:
        db.session.close_all()


@user_app.route('/update_user', methods=['POST'])
@role_required('Admin')
@jwt_required()
def update_user():
    """
        Route method to update existing user.
        input - JSON {first_name: '', last_name: '', email: '', role: ''}
    """
    try:
        params = request.get_json()
        try:
            required_dict = {
                "email": params.get("email", None),
                "first_name": params.get("first_name", None),
                "last_name": params.get("last_name", None),
                "role": params.get("role", None)
            }

            if None not in required_dict.values() and "" not in required_dict.values():
                db.session.query(User).filter(User.email_id == required_dict.get("email", ""),
                                              User.is_active == True).update(
                    {"first_name": params.get("first_name", ""), "last_name": params.get("last_name", ""),
                     "role": params.get("role", "")})
                log.info("updated user - {0}".format(required_dict.get("email", "")))

                session_user = get_jwt_identity()
                log_entry = Audit(
                    user=session_user,
                    client_ip=str(request.remote_addr),
                    status="SUCCESS",
                    result="UPDATED USER",
                    task_id="",
                    request_uri=str(request.path),
                    application="USER"
                )
                db.session.add(log_entry)
                db.session.commit()

                return json.dumps(Response(status=True, message="User updated Successfully.", data={}).__dict__,
                                  cls=CustomJSONEncoder)
            else:
                return json.dumps(Response(status=False,
                                           message=REQUEST_PARAM_MSG,
                                           data={}).__dict__, cls=CustomJSONEncoder)
        except sqlalchemy.exc.IntegrityError as ie:
            log.error(str(ie))
            log.error(traceback.print_exc())
            return json.dumps(Response(status=False,
                                       message=SQL_INTEGRITY_MSG,
                                       data={}).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False,
                                   message=REQUEST_ERROR_MSG,
                                   data={}).__dict__, cls=CustomJSONEncoder)
    finally:
        db.session.close_all()
