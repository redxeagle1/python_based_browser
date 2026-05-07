import socket
import ssl


class URL:
    """desc:
    A URL is composed of scheme[http,http1.1...etc], A host [like google.com]
    and lastly the path which is like "mail.google.com/mail/"

    It can also contain extra info i.e ports,queries and fragments
    """

    def __init__(self, url: str):
        # getting the URL scheme
        self.scheme, url = url.split("://", 1)

        # checks for http or https scheme then idenifies the suitable port based on it
        assert self.scheme in ["http", "https"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        # if there is not url path assigned the concatinate the "/" with the url
        if "/" not in url:
            url = url + "/"

        # Getting the host
        self.host, url = url.split("/", 1)

        # Getting the path
        self.path = "/" + url

    def request(self):  # Telnet IN PYTHON
        """A socket has
        - address family, which tells you how to find the other computer.
        - type, which describes the sort of conversation that’s going to happen
        - protocol, which describes the steps by which the two computers
        will establish a connection.
        """

        # in order to support the https we will use ssl library which handles
        #  - which encryption algorithms are user-mode
        #  - how a common encryption key is agreed to
        #  - how to make sure that the browser is connecting to the correct host.

        # we will creae context obj that will wrap the sockent itself
        s = socket.socket(
            family=socket.AF_INET,  # Address families have names that begin with `AF`
            type=socket.SOCK_STREAM,  # Types have names that begin with `SOCK`.
            proto=socket.IPPROTO_TCP,  # Protocols have names that depend on the address family.
        )
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        # `connect` takes a single argument
        # that argument is a pair of a host and a port.
        # NOTE: different address families have different numbers of arguments.

        # request formating
        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
        request += "\r\n"

        # sending the request
        s.send(request.encode("utf8"))
        # getting the respone
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # split the response into pieces
        statusline = response.readline()
        version, status, epxplanation = statusline.split(" ", 2)

        # split each line at the first colon then
        # fill in a map of header names to header values.
        # NOTE:Headers are case-insensitive, so normalize them to lower case
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        # Headers can describe all sorts of information,
        # couple of headers are especially important because they tell us that the data
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        s.close()

        return content


def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


def load(url):
    body = url.request()
    show(body)
