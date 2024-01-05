from flask import request, Blueprint
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from flask_jwt_extended import jwt_required, get_jwt_identity
from Social.src.utils.helpers import role_required
from Social.src.utils.models import Audit, db, Politicians, Posts, Pages
from sqlalchemy.sql import func, extract, distinct
import json
import traceback
import logging as log

politicians_app = Blueprint('politicians_app', __name__)


@politicians_app.route('/add_politician', methods=['POST'])
@jwt_required()
@role_required(['Admin'])
def add_politician():
    """
        Route method for adding a new politicians.
        input - JSON {key:'', value: ''}
    """
    try:
        params = request.get_json()
        politician_name = params.get('politician_name', None)
        politician_img_url = params.get('politician_img_url', None)
        party_code = params.get('party_code', None)
        description = params.get('description', None)
        designation = params.get('designation', None)

        session_user = get_jwt_identity()

        if politician_name is None or len(politician_name.strip()) == 0:
            return json.dumps(Response(status=False, message="No Politician Name provided.", data={}).__dict__,
                              cls=CustomJSONEncoder)
        else:
            log.info("Add Politician entry - {0}".format(politician_name))
            log_entry = Audit(
                user=session_user,
                client_ip=str(request.remote_addr),
                status="SUCCESS",
                result="POLITICIAN SAVED",
                task_id="",
                request_uri=str(request.path),
                application="POLITICIAN"
            )
            db.session.add(log_entry)

            doc_rec = Politicians(politician_name=politician_name, politician_img_url=politician_img_url,
                                  party_code=party_code, description=description, designation=designation,
                                  created_by=session_user)
            db.session.add(doc_rec)
            db.session.commit()

        return json.dumps(Response(status=True, message="Politician record saved.", data={}).__dict__,
                          cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to save Politician.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@politicians_app.route('/delete_politician', methods=['POST'])
@jwt_required()
@role_required(['Admin'])
def delete_politician():
    """
        Route method for deleting an politician.
        input - JSON {politician_id:''}
    """
    try:
        params = request.get_json()
        politician_id = params.get('politician_id', None)
        session_user = get_jwt_identity()

        if politician_id is None or len(str(politician_id).strip()) == 0:
            return json.dumps(Response(status=False, message="No politician id provided.", data={}).__dict__,
                              cls=CustomJSONEncoder)
        else:
            log.info("Delete POLITICIAN entry - {0}".format(politician_id))
            log_entry = Audit(
                user=session_user,
                client_ip=str(request.remote_addr),
                status="SUCCESS",
                result="POLITICIAN DELETED",
                task_id="",
                request_uri=str(request.path),
                application="POLITICIAN"
            )
            db.session.add(log_entry)
            db.session.query(Politicians).filter(Politicians.politician_id == politician_id).delete()
            db.session.commit()

            return json.dumps(Response(status=True, message="Politician Deleted", data={}).__dict__,
                              cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to delete politician.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@politicians_app.route('/list_politicians', methods=['POST', 'GET'])
@jwt_required()
@role_required(['Admin'])
def list_politicians():
    """
        Route method for listing all politicians.
        input - JSON {}
    """
    try:
        if request.method == 'GET':
            state = request.args.get('state', None)
        else:
            params = request.get_json()
            state = params.get('state', None)

        docs = db.session.query(Politicians.politician_id, Politicians.politician_name, Politicians.politician_img_url,
                                Politicians.description, Politicians.designation, Politicians.party_code,
                                Politicians.created_on, Politicians.score, Politicians.activeness_group).where(
            func.trim(func.lower(Politicians.state_code)) == state.lower()).order_by(
            Politicians.politician_name, Politicians.score, Politicians.activeness_group).all()

        if len(docs) > 0:
            doc_fields = docs[0]._fields
        else:
            doc_fields = ["politician_id", "politician_name", "politician_img_url", "description", "designation",
                          "party_code", "created_on", "score", "activeness_group"]

        recs = [{your_key: getattr(x, your_key) for your_key in doc_fields} for x in docs]

        return json.dumps(Response(status=True, message="Data fetched", data=recs).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch politicians.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@politicians_app.route('/posts', methods=['POST', 'GET'])
@jwt_required()
@role_required(['Admin', 'User'])
def politician_posts():
    """
        Route method for listing all post of politician.
        input - JSON {}
    """
    try:
        if request.method == 'GET':
            politician_id = request.args.get('id', None)
        else:
            params = request.get_json()
            politician_id = params.get('id', None)

        platform_data = {}
        docs = db.session.query(Posts.post_id, Posts.post_content, Pages.page_id, Pages.page_name, Pages.platform_name,
                                Pages.politician_id, Posts.created_on, Posts.score, Posts.classification).where(
            Posts.page_id == Pages.page_id,
            Pages.politician_id == politician_id).limit(50).all()

        if len(docs) > 0:
            doc_fields = docs[0]._fields
        else:
            doc_fields = ["post_id", "post_content", "page_id", "page_name", "platform_name",
                          "politician_id", "created_on", "score", "classification"]

        recs = [{your_key: getattr(x, your_key) for your_key in doc_fields} for x in docs]

        for i in recs:
            p_name = i.get("platform_name", "")
            if p_name in list(platform_data.keys()):
                platform_data[p_name].append(i)
            else:
                platform_data[p_name] = []
                platform_data[p_name].append(i)

        return json.dumps(Response(status=True, message="Data fetched", data=platform_data).__dict__,
                          cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch posts.", data={}).__dict__,
                          cls=CustomJSONEncoder)
