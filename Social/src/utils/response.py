class Response(dict):
    def __init__(self, status, message, data=None):
        """
        :param status:
            boolean, True/False status for the request.
        :param message:
            string, Error/Success message to be displayed to the user.
        :param data:
            list, list of dict containing the data.
        """
        self.status = status
        self.message = message
        if data is None:
            self.data = []
        else:
            self.data = data
