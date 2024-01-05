import json
import datetime
import decimal


class CustomJSONEncoder(json.JSONEncoder):
    """
        Customer JSON encoder class to type cast the response data.
    """
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime.time):
            return str(o)

        return json.JSONEncoder.default(self, o)
