import socket
import ssl
import tkinter

# chosed because that was a common old-timey monitor size
WIDTH, HIEGT = 800, 600


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
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

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


class Browser:
    def __init__(self):
        # Creating the window and the canvas
        self.window = tkinter.Tk()  # creating the window
        """
        - this line creates the `Canvas` inside that window:
                - self.window as an argument, so that Tk knows where to display the canvas.
                - The other arguments define the canvas’s size"""
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HIEGT,
        )
        self.canvas.pack()  # a Tk peculiarity, positions the canvas inside the window.

    def load(self, url):
        # this loads our HTML text content for now...
        body = url.request()
        text = lex(body)
        # without these vars all the text chars will be drawn in the same place,evantual overlap!
        HSTEP, VSTEP = 13, 18  # these to control the cursor movements
        cursor_x, cursor_y = HSTEP, VSTEP  # the current cursor placement
        # this will draw in the canvas
        for c in text:
            self.canvas.create_text(
                cursor_x, cursor_y, text=c
            )  # will display text based on args passed as coordinate
            # the movement logic
            cursor_x += HSTEP
            if cursor_x >= WIDTH - HSTEP:
                cursor_y += VSTEP  # i.e Vertical steps
                cursor_x = HSTEP  # i.e Horizontical steps


def lex(body):
    in_tag = False
    text = ""
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text
