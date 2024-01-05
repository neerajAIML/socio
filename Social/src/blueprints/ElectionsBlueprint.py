from flask import request, Blueprint
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from flask_jwt_extended import jwt_required, get_jwt_identity
from Social.src.utils.helpers import role_required
from Social.src.utils.models import db, PartyInPower, Parties, PlatformUsers, Posts, Comments
from sqlalchemy.sql import func, extract, distinct
import json
import traceback
import logging as log

elections_app = Blueprint('elections_app', __name__)


@elections_app.route('/get_parties_in_power', methods=['GET', 'POST'])
@jwt_required()
@role_required(['Admin'])
def get_parties_in_power():
    """
        Route method for getting platform details.
        input - JSON {key:'', value: ''}
    """
    try:
        # session_user = get_jwt_identity()
        _records = db.session.query(PartyInPower.party_code, PartyInPower.state_code, Parties.color).where(
            Parties.party_code == PartyInPower.party_code).all()

        if len(_records) > 0:
            _fields = _records[0]._fields
        else:
            _fields = ["party_code", "state_code", "color"]

        _recs = [{your_key: getattr(x, your_key) for your_key in _fields} for x in _records]
        return json.dumps(Response(status=True, message="Parties records retrieved.", data=_recs).__dict__,
                          cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch parties data.", data={}).__dict__,
                          cls=CustomJSONEncoder)
