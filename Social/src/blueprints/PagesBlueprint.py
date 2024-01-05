from flask import request, Blueprint
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from flask_jwt_extended import jwt_required, get_jwt_identity
from Social.src.utils.helpers import role_required
from Social.src.utils.models import Audit, db, Pages
import json
import traceback
import logging as log

pages_app = Blueprint('pages_app', __name__)


@pages_app.route('/add_page', methods=['POST'])
@jwt_required()
@role_required(['Admin'])
def add_page():
    """
        Route method for adding a new pages.
        input - JSON {key:'', value: ''}
    """
    try:
        params = request.get_json()
        page_name = params.get('page_name', None)
        page_url = params.get('page_url', None)
        description = params.get('description', None)
        platform_name = params.get('platform_name', None)
        politician_id = params.get('politician_id', 1)

        session_user = get_jwt_identity()

        if page_name is None or len(page_name.strip()) == 0:
            return json.dumps(Response(status=False, message="No Page Name provided.", data={}).__dict__,
                              cls=CustomJSONEncoder)
        else:
            log.info("Add Politician entry - {0}".format(page_name))
            log_entry = Audit(
                user=session_user,
                client_ip=str(request.remote_addr),
                status="SUCCESS",
                result="PAGE SAVED",
                task_id="",
                request_uri=str(request.path),
                application="PAGE"
            )
            db.session.add(log_entry)

            doc_rec = Pages(page_name=page_name, page_url=page_url, platform_name=platform_name,
                            politician_id=politician_id, description=description, created_by=session_user)
            db.session.add(doc_rec)
            db.session.commit()

        return json.dumps(Response(status=True, message="Page record saved.", data={}).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to save page.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@pages_app.route('/delete_page', methods=['POST'])
@jwt_required()
@role_required(['Admin'])
def delete_page():
    """
        Route method for deleting an page.
        input - JSON {page_id:''}
    """
    try:
        params = request.get_json()
        page_id = params.get('page_id', None)
        session_user = get_jwt_identity()

        if page_id is None or len(str(page_id).strip()) == 0:
            return json.dumps(Response(status=False, message="No page id provided.", data={}).__dict__,
                              cls=CustomJSONEncoder)
        else:
            log.info("Delete page entry - {0}".format(page_id))
            log_entry = Audit(
                user=session_user,
                client_ip=str(request.remote_addr),
                status="SUCCESS",
                result="page DELETED",
                task_id="",
                request_uri=str(request.path),
                application="page"
            )
            db.session.add(log_entry)
            db.session.query(Pages).filter(Pages.page_id == page_id).delete()
            db.session.commit()

            return json.dumps(Response(status=True, message="Page Deleted", data={}).__dict__,
                              cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to delete page.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@pages_app.route('/list_pages', methods=['POST', 'GET'])
@jwt_required()
@role_required(['Admin'])
def list_pages():
    """
        Route method for listing all pages.
        input - JSON {}
    """
    try:
        docs = db.session.query(Pages.page_id, Pages.page_name, Pages.page_url,
                                Pages.description, Pages.platform_name, Pages.politician_id,
                                Pages.created_on).order_by(Pages.page_name).all()

        if len(docs) > 0:
            doc_fields = docs[0]._fields
        else:
            doc_fields = ["page_id", "page_name", "page_url", "description", "platform_name",
                          "politician_id", "created_on"]

        recs = [{your_key: getattr(x, your_key) for your_key in doc_fields} for x in docs]

        return json.dumps(Response(status=True, message="Data fetched", data=recs).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch pages.", data={}).__dict__,
                          cls=CustomJSONEncoder)
