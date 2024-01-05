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
from sqlalchemy import text

import imp
from flask import Flask, request, jsonify
import requests
#from facebook import facebookScrap
from waitress import serve
from time import pthread_getcpuclockid, sleep
from Social.src.configurations import settings
from Social.src.blueprints.facebook import facebookScrap

facebook_app = Blueprint('facebook_app', __name__)
REQUEST_ERROR_MSG = "Error while processing Request."
SQL_INTEGRITY_MSG = "Duplicate record."
REQUEST_PARAM_MSG = "Invalid data provided, please check all fields are provide and they are not empty."


@facebook_app.route('/livefeed', methods=['POST', 'GET'])
#@role_required('Admin')
#@jwt_required()
def livefeed():
    """
        Route method to list all users..
        input - JSON {}
    """
    try:
        # obj = facebookScrap()
        # data = obj.insertData('output_bjp4indiafacebook20231227-132818.xlsx')
        # print(data)

        obj = facebookScrap()
        # Call the my_function method
        data = request.json  # status code
        #{"userName":"neeraj88maurya21","passWord":"Admin@del21","page":"https://www.instagram.com/bjp4india/","pageName":"bjp4india"}
        if settings.facebook_name and settings.facebook_password and data['page'] and data['pageName']:
            driver = obj.login(settings.facebook_name,settings.facebook_password)
            print(driver)
            page = data['page']
            page_name = data['pageName']
            no_of_page = data['no_of_page']
            print("Before starting",no_of_page)
            if no_of_page==0:
                no_of_page = 1
                print("No of pages",no_of_page)
            
            fileName = obj.scrap_post(driver,page,page_name,no_of_page)
            print(fileName) 
            obj.dataPutIntoDatabase(driver,fileName)

            #####-Data Insert into database-#####
            databaseObj = facebookScrap()
            print("files Name of the database")
            print('output_'+fileName)
            data = databaseObj.insertData('output_'+fileName)

        
        return json.dumps(Response(status=False, message="testing hete"))
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)))
@facebook_app.route('post/', methods=['GET'])
#@jwt_required()
#@role_required(['Admin'])
def fPost():
    try:
        query = f"""    
                SELECT * FROM posts
        """
       
        query = text(query)
        result = db.session.execute(query).fetchall()
        
        allDict = list()
        for row in result:
            dict = {}
            dict['page_id']=row[0]
            dict['post_content']=row[1]
            dict['created_on']=row[2]
            dict['created_by']=row[3]
            dict['classification']=row[4]
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
