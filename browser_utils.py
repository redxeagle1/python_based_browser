import socket


class URL:
    """desc:
    A URL is composed of scheme[http,http1.1...etc], A host [like google.com]
    and lastly the path which is like "mail.google.com/mail/"

    It can also contain extra info i.e ports,queries and fragments
    """

    def __init__(self, url: str):
        # getting the URL scheme
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"

        # if there is not url path assigned the concatinate the "/" with the url
        if "/" not in url:
            url = url + "/"

        # Getting the host
        self.host, url = url.split("/", 1)

        # Getting the path
        self.path = "/" + url

    def request(self):
