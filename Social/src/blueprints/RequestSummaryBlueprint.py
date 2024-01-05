from flask import Blueprint
from flask import request, send_file
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from Social.src.utils.response import Response
from Social.src.utils.helpers import role_required
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from Social.src.utils.models import db
from sqlalchemy.sql import func, extract, distinct
from sqlalchemy.sql.elements import Label
from sqlalchemy import desc
from collections import Counter
import json
import logging as log
import traceback
import pandas as pd
import os

summary_app = Blueprint('summary_app', __name__)
OPERATION_SUCCESS = "Operation Successful"


@summary_app.route('/donut_chart', methods=['POST'])
@jwt_required()
@role_required(['Admin', 'User'])
def get_donut_chart():
    try:
        filters = request.get_json()
        year = filters.get("year", None)
        month = filters.get("month", None)

        summary_records_liked = db.session.query(func.count(Responses.response_id).label("total_count"),
                                           func.count(Responses.is_liked).label("count"),
                                           UserQueries.month).where(
            UserQueries.year==year,
            UserQueries.month == month,
            Responses.query_id == UserQueries.query_id, Responses.is_liked==True).group_by(UserQueries.month).all()

        summary_records_disliked = db.session.query(func.count(Responses.response_id).label("total_count"),
                                           func.count(Responses.is_disliked).label("count"),
                                           UserQueries.month).where(
            UserQueries.year==year,
            UserQueries.month == month,
            Responses.query_id == UserQueries.query_id, Responses.is_disliked==True).group_by(UserQueries.month).all()

        liked_records = db.session.query(Responses.query_id).where(UserQueries.year == year, UserQueries.month == month,
                                                                   Responses.query_id == UserQueries.query_id,
                                                                   Responses.is_liked == True).all()

        disliked_records = db.session.query(Responses.query_id).where(UserQueries.year == year,
                                                                      UserQueries.month == month,
                                                                      Responses.query_id == UserQueries.query_id,
                                                                      Responses.is_disliked == True).all()

        nofeedback_records = db.session.query(Responses.query_id).where(UserQueries.year == year,
                                                                        UserQueries.month == month,
                                                                        Responses.query_id == UserQueries.query_id,
                                                                        Responses.is_liked == False,
                                                                        Responses.is_disliked == False).all()

        query_id_with_response = list()
        query_id_with_response.extend([getattr(x, "query_id") for x in liked_records])
        query_id_with_response.extend([getattr(x, "query_id") for x in disliked_records])
        query_id_with_response = set(query_id_with_response)
        query_ids_with_nofeedback = set([getattr(x, "query_id") for x in nofeedback_records])
        remaining_query_id = query_ids_with_nofeedback - query_id_with_response

        support_records = db.session.query(func.count(SupportTickets.support_id).label("count"),
                                            SupportTickets.month).where(SupportTickets.year == year,
                                                                        SupportTickets.month == month).group_by(
            SupportTickets.month).all()

        if len(support_records) > 0:
            support_fields_liked = support_records[0]._fields
        else:
            support_fields_liked = ["total_count", "count", "month"]

        recs_support = [{your_key: getattr(x, your_key) for your_key in support_fields_liked} for x in
                      support_records]

        if len(summary_records_liked) > 0:
            summary_fields_liked = summary_records_liked[0]._fields
        else:
            summary_fields_liked = ["total_count", "count", "month"]

        if len(summary_records_disliked) > 0:
            summary_fields_dis_liked = summary_records_disliked[0]._fields
        else:
            summary_fields_dis_liked = ["total_count", "count", "month"]

        recs_liked = [{your_key: getattr(x, your_key) for your_key in summary_fields_liked} for x in
                      summary_records_liked]

        recs_dis_liked = [{your_key: getattr(x, your_key) for your_key in summary_fields_dis_liked} for x in
                          summary_records_disliked]

        if len(recs_liked) > 0:
            liked_count = recs_liked[0].get("count")
        else:
            liked_count = 0

        if len(recs_dis_liked) > 0:
            disliked_count = recs_dis_liked[0].get("count")
        else:
            disliked_count = 0

        nofeedback_count = len(remaining_query_id)

        if len(recs_support) > 0:
            support_count = recs_support[0].get("count")
        else:
            support_count = 0

        total_count = liked_count + disliked_count + nofeedback_count + support_count

        resp = {
            "total_files": total_count,
            "donutChartdata": {
                "series": [liked_count, disliked_count, nofeedback_count, support_count],
                "labels": ["Liked", "Disliked", "No Feedback", "Support Emails"],
                "title": "Monthly Distribution of User’s Feedback and Support Emails",
                "description": "Above chart shows the total number of responses having Liked, Disliked, No Feedback & Support Mails."
            }
        }
        return json.dumps(Response(status=True, message="Operation Successful.", data=resp).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)).__dict__, cls=CustomJSONEncoder)


@summary_app.route('/filters', methods=['GET'])
@jwt_required()
@role_required(['Admin', 'User'])
def filters():
    records = db.session.query(UserQueries.year).order_by(UserQueries.year).distinct().all()
    years = [{"value": x[0], "viewValue": x[0], "defaultSelection": False} for x in records]
    if len(years) > 0:
        years[-1]["defaultSelection"] = True

    month_records = db.session.query(UserQueries.month).order_by(UserQueries.month).distinct().all()
    months = [{"value": x[0], "viewValue": x[0], "defaultSelection": False} for x in month_records]
    if len(months) > 0:
        months[-1]["defaultSelection"] = True

    try:
        filters = {
            "filterData": {
                "years": years,
                "months": months,
                "category": []
            }
        }

        return json.dumps(Response(status=True, message=OPERATION_SUCCESS, data=filters).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)).__dict__, cls=CustomJSONEncoder)


@summary_app.route('/line_chart', methods=['POST'])
@jwt_required()
@role_required(['Admin', 'User'])
def get_line_chart():
    filters = request.get_json()
    year = filters.get("year", None)

    try:
        summary_records = db.session.query(func.count(UserQueries.query_id).label("total"),
                                           UserQueries.year, UserQueries.month).where(
            UserQueries.year == year).group_by(UserQueries.year, UserQueries.month).order_by(UserQueries.month).all()

        support_records = db.session.query(func.count(SupportTickets.support_id).label("total"),
                                           SupportTickets.year, SupportTickets.month).where(
            SupportTickets.year == year).group_by(SupportTickets.year, SupportTickets.month).order_by(SupportTickets.month).all()

        months = list()
        month_num = list()
        if len(summary_records) > 0:
            summary_fields = summary_records[0]._fields
            recs = [{your_key: getattr(x, your_key) for your_key in summary_fields} for x in summary_records]
            grouped_df = pd.DataFrame(recs)
            months = ["Month {0}".format(str(x)) for x in grouped_df["month"].tolist()]
            month_num = grouped_df["month"].tolist()
            f_ids = grouped_df["total"].tolist()

        support_ids = list()
        if len(support_records) > 0:
            support_fields = support_records[0]._fields
            s_recs = [{your_key: getattr(x, your_key) for your_key in support_fields} for x in support_records]
            for m in month_num:
                check = True
                for r in s_recs:
                    if r.get("month", None) == m:
                        support_ids.append(r.get("total", 0))
                        check = False

                if check is True:
                    support_ids.append(0)
        else:
            support_ids = [0 for x in months]

        resp = {
            "lineChartdata": {
            "series": [{
                        "name": "Total Queries",
                        "data": f_ids
                    }, {
                        "name": "Total Support Emails",
                        "data": support_ids
                    }],
                "categories": months,
                "title": "Monthly User Queries and Emails",
                "description": "Above chart shows the total number of queries requested by users, grouped by month."
            }
        }

        return json.dumps(Response(status=True, message=OPERATION_SUCCESS, data=resp).__dict__,
                          cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)).__dict__, cls=CustomJSONEncoder)


@summary_app.route('/stack_chart', methods=['POST'])
@jwt_required()
@role_required(['Admin', 'User'])
def get_stack_chart():
    filters = request.get_json()
    month = filters.get("month", None)
    year = filters.get("year", None)

    try:
        summary_records = db.session.query(UserQueries.year, UserQueries.month,
                                           func.count(Responses.response_id).label("total_count"), Responses.category,
                                           Responses.doc_type).where(UserQueries.year==year, UserQueries.month==month,
                                             UserQueries.query_id==Responses.query_id).group_by(
            UserQueries.year, UserQueries.month, Responses.category, Responses.doc_type).all()

        if len(summary_records) > 0:
            summary_fields = summary_records[0]._fields
        else:
            summary_fields = ["year", "month", "total_count", "category", "doc_type"]

        resp = {
            "stackBarChartdata": {
                "series": [],
                "categories": [],
                "title": "Response Category & Document Type Processed",
                "description": "Above chart shows the total queries grouped by category & doc_type.",
                "stacked": True
            }
        }

        db_recs = [{your_key: getattr(x, your_key) for your_key in summary_fields} for x in summary_records]
        df = pd.DataFrame(db_recs)
        if len(db_recs):
            stack_df = df.pivot(index='category', columns='doc_type', values='total_count')
            stack_df.fillna(0, inplace=True)
            t_ids = stack_df.index.tolist()
            recs = stack_df.to_dict("list")
            resp["stackBarChartdata"]["categories"] = t_ids
            for k in recs.keys():
                resp["stackBarChartdata"]["series"].append({"name": k, "data": recs[k]})

        return json.dumps(Response(status=True, message=OPERATION_SUCCESS, data=resp).__dict__, cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)).__dict__, cls=CustomJSONEncoder)


@summary_app.route('/summary_table', methods=['POST'])
@jwt_required()
@role_required(['Admin', 'User'])
def summary_table():
    filters = request.get_json()
    month = filters.get("month", None)
    year = filters.get("year", None)

    try:
        summary_records = db.session.query(UserQueries.query_id, UserQueries.year, UserQueries.month, UserQueries.created_on,
                                           UserQueries.query).where(
            UserQueries.year==year, UserQueries.month==month).order_by(desc(UserQueries.created_on)).all()

        if len(summary_records) > 0:
            summary_fields = summary_records[0]._fields
        else:
            summary_fields = ["query_id", "year", "month", "created_on", "query"]

        recs = [{your_key: getattr(x, your_key) for your_key in summary_fields} for x in summary_records]

        return json.dumps(Response(status=True, message=OPERATION_SUCCESS, data={"records": recs}).__dict__,
                          cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)).__dict__, cls=CustomJSONEncoder)


@summary_app.route('/query_map', methods=['POST'])
@jwt_required()
@role_required(['Admin', 'User'])
def query_map():
    filters = request.get_json()
    month = filters.get("month", None)
    year = filters.get("year", None)

    try:
        summary_records = db.session.query(UserQueries.query_id, UserQueries.year, UserQueries.month, UserQueries.created_on,
                                           UserQueries.query, UserQueries.phrases).where(
            UserQueries.year==year, UserQueries.month==month).order_by(desc(UserQueries.created_on)).all()

        if len(summary_records) > 0:
            summary_fields = summary_records[0]._fields
        else:
            summary_fields = ["query_id", "year", "month", "created_on", "query", "phrases"]

        recs = [{your_key: getattr(x, your_key) for your_key in summary_fields} for x in summary_records]

        phrases_list = [x for y in recs for x in y.get("phrases", "").split(";")]
        map_data = dict(Counter(phrases_list))
        map_list = [{"x": key, "y": map_data.get(key, 0)} for key in map_data.keys()]

        chart_map = {
            "series": [{"data": map_list}],
            "chart": {
                "height": 350,
                "type": "treemap"
            },
            "plotOptions": {
                "treemap": {
                    "enableShades": True,
                    "shadeIntensity": 0.5,
                    "reverseNegativeShade": True
                }
            },
            "colors": ["#0069b9"],
            "title": {
                "text": "Query Map"
            },
            "description": "Above chart shows the count of similar key phrases used by users while searching.",
        }

        return json.dumps(Response(status=True, message=OPERATION_SUCCESS, data=chart_map).__dict__,
                          cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)).__dict__, cls=CustomJSONEncoder)


@summary_app.route('/document_count', methods=['GET', 'POST'])
@jwt_required()
@role_required(['Admin', 'User'])
def document_count():
    try:
        summary_records = db.session.query(func.count(Documents.doc_id).label("count")).where(
            Documents.is_indexed == True, Documents.is_active == True).all()

        if len(summary_records) > 0:
            summary_fields = summary_records[0]._fields
        else:
            summary_fields = ["count"]

        recs = [{your_key: getattr(x, your_key) for your_key in summary_fields} for x in summary_records]

        return json.dumps(
            Response(status=True, message=OPERATION_SUCCESS, data={"count": recs[0].get("count", 0)}).__dict__,
            cls=CustomJSONEncoder)
    except Exception as ex:
        log.error(str(ex))
        log.error(traceback.print_exc())
        return json.dumps(Response(status=False, message=str(ex)).__dict__, cls=CustomJSONEncoder)
