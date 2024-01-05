from flask import request, Blueprint, jsonify, send_from_directory
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from flask_jwt_extended import jwt_required, get_jwt_identity
from Social.src.utils.helpers import role_required
from Social.src.utils.models import db, States
import json
import traceback
import logging as log
from sqlalchemy import text

states_app = Blueprint('states_app', __name__)


@states_app.route('/add_state', methods=['POST'])
@jwt_required()
@role_required(['Admin'])
def add_state():
    """
        Route method for adding a new abbreviation.
        input - JSON {key:'', value: ''}
    """
    try:
        params = request.get_json()
        name = params.get('name', None)
        description = params.get('description', None)
        lat = float(params.get('lat', 0.0))
        long = float(params.get('long', 0.0))

        session_user = get_jwt_identity()

        if name is None or len(name.strip()) == 0:
            return json.dumps(Response(status=False, message="No name provided.", data={}).__dict__,
                              cls=CustomJSONEncoder)
        else:
            log.info("Add State entry - {0}".format(name))
            doc_rec = States(state_name=name, description=description, lat=lat, long=long, created_by=session_user)
            db.session.add(doc_rec)
            db.session.commit()

        return json.dumps(Response(status=True, message="Abbreviations saved.", data={}).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to save abbreviations.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@states_app.route('/delete_state', methods=['POST'])
@jwt_required()
@role_required(['Admin'])
def delete_state():
    """
        Route method for deleting an abbreviation.
        input - JSON {abbr_id:''}
    """
    try:
        params = request.get_json()
        state_id = params.get('state_id', None)
        session_user = get_jwt_identity()

        if state_id is None or len(str(state_id).strip()) == 0:
            return json.dumps(Response(status=False, message="No state id provided.", data={}).__dict__,
                              cls=CustomJSONEncoder)
        else:
            log.info("Delete state entry - {0}".format(state_id))
            db.session.query(States).filter(States.state_id == state_id).delete()
            db.session.commit()

            return json.dumps(Response(status=True, message="Abbreviations Deleted", data={}).__dict__,
                              cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to delete Abbreviations.", data={}).__dict__,
                          cls=CustomJSONEncoder)


@states_app.route('/list_states', methods=['POST', 'GET'])
@jwt_required()
@role_required(['Admin'])
def list_states():
    """
        Route method for listing all states.
        input - JSON {}
    """
    try:
        docs = db.session.query(States.state_code, States.state_name, States.description, States.created_by,
                                States.created_on, States.lat, States.long).order_by(States.state_name).all()

        if len(docs) > 0:
            doc_fields = docs[0]._fields
        else:
            doc_fields = ["state_code", "state_name", "description", "created_by", "created_on", "lat", "long"]

        recs = [{your_key: getattr(x, your_key) for your_key in doc_fields} for x in docs]

        return json.dumps(Response(status=True, message="Data fetched", data=recs).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch states.", data={}).__dict__,
                          cls=CustomJSONEncoder)

@states_app.route('/<state_id>/party/<party_id>/platform/feed', methods=['GET'])
#@jwt_required()
#@role_required(['Admin'])
def plateformDashboard(state_id, party_id):
    try:
        limits  = request.args.get('limit')
        print(limits)
        if not state_id and not party_id:
                return jsonify({"message": "State_id and party_id is required in the URL parameters"}), 400
        if limits:
            query = f"""    
                SELECT comments.comment_id, 
                platform_users.platform_name,
                count(DISTINCT comments.post_id) as totalPost,
                count(comments.classification) as comment,
                sum(CASE WHEN classification=='Pro Government' THEN 1 ELSE 0 END) as proGov,
                sum(CASE WHEN classification=='Anti Government' THEN 1 ELSE 0 END) as antiGov
                FROM platform_users
                    INNER JOIN comments
                        ON comments.email_id = platform_users.email_id
                        WHERE state_code like '%{state_id}%'
                        GROUP by platform_users.platform_name
                        LIMIT {limits}
            """
        else:
            query = f"""    
                SELECT comments.comment_id, 
                platform_users.platform_name,
                count(DISTINCT comments.post_id) as totalPost,
                count(comments.classification) as comment,
                sum(CASE WHEN classification=='Pro Government' THEN 1 ELSE 0 END) as proGov,
                sum(CASE WHEN classification=='Anti Government' THEN 1 ELSE 0 END) as antiGov
                FROM platform_users
                    INNER JOIN comments
                        ON comments.email_id = platform_users.email_id
                        WHERE state_code like '%{state_id}%'
                        GROUP by platform_users.platform_name
                """
        query = text(query)
        result = db.session.execute(query).fetchall()
        print(result)
        
        allDict = list()
        for row in result:
            dict = {}
            if row[1]=="Facebook":
                dict['plateform']='Facebook'
                dict['total-feeds']=row[2]
                dict['total-comments']=row[3]
                dict['Pro-comments']=row[4]
                dict['anit-comments']=row[5]

            if row[1]=="Instagram":
                dict['plateform']='Instagram'
                dict['total-feeds']=row[2]
                dict['total-comments']=row[3]
                dict['Pro-comments']=row[4]
                dict['anit-comments']=row[5]

            if row[1]=="Twitter - X":
                dict['plateform']='Twitter - X'
                dict['total-feeds']=row[2]
                dict['total-comments']=row[3]
                dict['Pro-comments']=row[4]
                dict['anit-comments']=row[5]
            allDict.append(dict)
        # print(allDict)
        # print(f"{state_id} and {party_id}")
        return json.dumps(Response(status=True, message="Data fetched", data=allDict).__dict__, cls=CustomJSONEncoder)

    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch states.", data={}).__dict__,
                          cls=CustomJSONEncoder)

@states_app.route('/<state_id>/party/<party_id>/platform/<plateform_id>/feed', methods=['GET'])
#@jwt_required()
#@role_required(['Admin'])
def postSummary(state_id, party_id,plateform_id):
    try:
        limits  = request.args.get('limit')
        print(limits)
        if not state_id and not party_id and not plateform_id:
                return jsonify({"message": "State_id and party_id is required in the URL parameters"}), 400
        if limits:
            query = f"""    
                SELECT 
                    DISTINCT posts.post_id,
                    substr(posts.post_content,0,30) as summary,
                    (SELECT count(*) FROM comments WHERE comments.post_id=posts.page_id) as commentsCount,
                    (SELECT sum(CASE WHEN comments.classification=='Pro Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as proGov,
                    (SELECT sum(CASE WHEN comments.classification=='Anti Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as antiGov, 
                    posts.created_on
                    FROM posts
                    INNER JOIN comments
                        ON comments.post_id=posts.page_id
                    INNER JOIN platform_users
                        ON platform_users.email_id=comments.email_id
                    WHERE platform_users.platform_name like '%{plateform_id}%' AND platform_users.state_code like '%{state_id}%'
                    LIMIT {limits}
            """
        else:
            query = f"""    
                SELECT 
                    DISTINCT posts.post_id,
                    substr(posts.post_content,0,30) as summary,
                    (SELECT count(*) FROM comments WHERE comments.post_id=posts.page_id) as commentsCount,
                    (SELECT sum(CASE WHEN comments.classification=='Pro Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as proGov,
                    (SELECT sum(CASE WHEN comments.classification=='Anti Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as antiGov, 
                    posts.created_on
                    FROM posts
                    INNER JOIN comments
                        ON comments.post_id=posts.page_id
                    INNER JOIN platform_users
                        ON platform_users.email_id=comments.email_id
                    WHERE platform_users.platform_name like '%{plateform_id}%' AND platform_users.state_code like '%{state_id}%'
                    
                """
        query = text(query)
        result = db.session.execute(query).fetchall()
        print(result)
        
        allDict = list()
        for row in result:
            dict = {}
            dict['plateform']='Facebook'
            dict['id']=row[0]
            dict['feed-summary']=row[1]
            dict['total-comments']=row[2]
            dict['Pro-comments']=row[3]
            dict['anit-comments']=row[4]
            dict['time']=row[5]
            allDict.append(dict)
        # print(allDict)
        # print(f"{state_id} and {party_id}")
        return json.dumps(Response(status=True, message="Data fetched", data=allDict).__dict__, cls=CustomJSONEncoder)

    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch states.", data={}).__dict__,
                          cls=CustomJSONEncoder)
    
@states_app.route('/<state_id>/party/<party_id>/platform/<plateform_id>/feed/<feed_id>', methods=['GET'])
#@jwt_required()
#@role_required(['Admin'])
def postOny(state_id, party_id,plateform_id,feed_id):
    try:
        limits  = request.args.get('limit')
        if not state_id and not party_id and not plateform_id:
                return jsonify({"message": "State_id and party_id is required in the URL parameters"}), 400
        
        query = f"""    
            SELECT 
                DISTINCT posts.post_id,
                posts.post_content,
                comments.comment_content,
                comments.classification,
                comments.user,
                comments.score
                FROM posts
                INNER JOIN comments
                    ON comments.post_id=posts.page_id
                INNER JOIN platform_users
                    ON platform_users.email_id=comments.email_id
                WHERE platform_users.platform_name like '%{plateform_id}%' AND platform_users.state_code like '%{state_id}%' AND posts.post_id={feed_id}
                
        """
       
        query = text(query)
        result = db.session.execute(query).fetchall()
        print(result)
        
        allDict = list()
        for row in result:
            dict = {}
            dict['plateform']='Facebook'
            dict['id']=row[0]
            dict['feed-summary']=row[1]
            dict['comments']=row[2]
            dict['sentiment']=row[3]
            dict['user-name']=row[4]
            dict['score']=row[5]
            allDict.append(dict)
        # print(allDict)
        # print(f"{state_id} and {party_id}")
        return json.dumps(Response(status=True, message="Data fetched", data=allDict).__dict__, cls=CustomJSONEncoder)

    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch states.", data={}).__dict__,
                          cls=CustomJSONEncoder)
    

@states_app.route('polytician/<polytician_id>/platform/<plateform_id>/feed', methods=['GET'])
#@jwt_required()
#@role_required(['Admin'])
def DemocracyPoliticianPlateform(polytician_id,plateform_id):
    try:
        limits  = request.args.get('limit')
        if not polytician_id and not plateform_id:
                return jsonify({"message": "State_id and party_id is required in the URL parameters"}), 400
        
        query = f"""    
                SELECT 
                DISTINCT posts.post_id,
                substr(posts.post_content,0,30) as summary,
                (SELECT count(*) FROM comments WHERE comments.post_id=posts.page_id) as commentsCount,
                (SELECT sum(CASE WHEN comments.classification=='Pro Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as proGov,
                (SELECT sum(CASE WHEN comments.classification=='Anti Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as antiGov, 
                posts.score as score

                FROM posts
                INNER JOIN pages
                ON pages.page_id=posts.page_id
                WHERE Pages.politician_id == {polytician_id} and pages.platform_name like '%{plateform_id}%'
                
        """
       
        query = text(query)
        result = db.session.execute(query).fetchall()
        print(result)
        
        allDict = list()
        for row in result:
            dict = {}
            dict['plateform']=plateform_id
            dict['id']=row[0]
            dict['feed-summary']=row[1]
            dict['comments_count']=row[2]
            dict['pro']=row[3]
            dict['anti']=row[4]
            dict['score']=row[5]
            allDict.append(dict)
        # print(allDict)
        # print(f"{state_id} and {party_id}")
        return json.dumps(Response(status=True, message="Data fetched", data=allDict).__dict__, cls=CustomJSONEncoder)

    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch states.", data={}).__dict__,
                          cls=CustomJSONEncoder)

@states_app.route('polytician/<polytician_id>/platform/feed', methods=['GET'])
#@jwt_required()
#@role_required(['Admin'])
def DemocracyPolitician(polytician_id):
    try:
        limits  = request.args.get('limit')
        if not polytician_id:
                return jsonify({"message": "State_id and party_id is required in the URL parameters"}), 400
        
        query = f"""    
                SELECT 
                DISTINCT posts.post_id,
                substr(posts.post_content,0,30) as summary,
                (SELECT count(*) FROM comments WHERE comments.post_id=posts.page_id) as commentsCount,
                (SELECT sum(CASE WHEN comments.classification=='Pro Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as proGov,
                (SELECT sum(CASE WHEN comments.classification=='Anti Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as antiGov, 
                posts.score as score,
                pages.platform_name
                FROM posts
                INNER JOIN pages
                ON pages.page_id=posts.page_id
                WHERE Pages.politician_id == {polytician_id}
                
        """
       
        query = text(query)
        result = db.session.execute(query).fetchall()
        print(result)
        
        allDict = list()
        for row in result:
            dict = {}
            
            dict['id']=row[0]
            dict['feed-summary']=row[1]
            dict['comments_count']=row[2]
            dict['pro']=row[3]
            dict['anti']=row[4]
            dict['score']=row[5]
            dict['plateform']=row[6]
            allDict.append(dict)
        # print(allDict)
        # print(f"{state_id} and {party_id}")
        return json.dumps(Response(status=True, message="Data fetched", data=allDict).__dict__, cls=CustomJSONEncoder)

    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch states.", data={}).__dict__,
                          cls=CustomJSONEncoder)

@states_app.route('polytician/<polytician_id>/dashboard/feed', methods=['GET'])
#@jwt_required()
#@role_required(['Admin'])
def DemocracyPoliticianPlateformSummary(polytician_id):
    try:
        limits  = request.args.get('limit')
        if not polytician_id:
                return jsonify({"message": "State_id and party_id is required in the URL parameters"}), 400
        
        query = f"""    
                SELECT 

                substr(posts.post_content,0,30) as summary,
                (SELECT count(*) FROM comments WHERE comments.post_id=posts.page_id) as commentsCount,
                (SELECT sum(CASE WHEN comments.classification=='Pro Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as proGov,
                (SELECT sum(CASE WHEN comments.classification=='Anti Government' THEN 1 ELSE 0 END) as proGov  FROM comments WHERE comments.post_id=posts.page_id) as antiGov, 
                pages.platform_name

                FROM posts
                INNER JOIN pages
                ON pages.page_id=posts.page_id
                WHERE Pages.politician_id == {polytician_id}
                
        """
        
        query = text(query)
        result = db.session.execute(query).fetchall()
        print(result)
        
        allDict = list()
        facebook = { "platform": "facebook", 
                    "total-feeds": 0, 
                    "total-comments": 0, 
                    "pro-comments": 0, 
                    "anti-comments": 0 
                    }
        insta =   { "platform": "insta", 
                    "total-feeds": 0, 
                    "total-comments": 0, 
                    "pro-comments": 0, 
                    "anti-comments": 0 
                    }
        twitter = { "platform": "twitter", 
                    "total-feeds": 0, 
                    "total-comments": 0, 
                    "pro-comments": 0, 
                    "anti-comments": 0 
                    }
        print(type(facebook))
        for row in result:
            if row[4]=='Facebook':
                facebook['total-feeds']=int(facebook['total-feeds'])+1
                facebook['total-comments']=facebook['total-comments']+row[1]
                facebook['pro-comments']=facebook['pro-comments']+row[2]
                facebook['anti-comments']=facebook['anti-comments']+row[3]
            if row[4]=='Twitter - X':
                twitter['total-feeds']=int(twitter['total-feeds'])+1
                twitter['total-comments']=twitter['total-comments']+row[1]
                twitter['pro-comments']=twitter['pro-comments']+row[2]
                twitter['anti-comments']=twitter['anti-comments']+row[3]
            if row[4]=='Instagram':
                insta['total-feeds']=int(insta['total-feeds'])+1
                insta['total-comments']=insta['total-comments']+row[1]
                insta['pro-comments']=insta['pro-comments']+row[2]
                insta['anti-comments']=insta['anti-comments']+row[3]
        
        allDict.append(facebook)
        allDict.append(twitter)
        allDict.append(insta)
        
        return json.dumps(Response(status=True, message="Data fetched", data=allDict).__dict__, cls=CustomJSONEncoder)

    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message="Unable to fetch states.", data={}).__dict__,
                          cls=CustomJSONEncoder)