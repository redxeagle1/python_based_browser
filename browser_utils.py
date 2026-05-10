import socket
import ssl
import tkinter as tk

# chosed because that was a common old-timey monitor size
WIDTH, HEIGHT = 800, 600
# without these vars all the text chars will be drawn in the same place,evantual overlap!
HSTEP, VSTEP = 13, 18  # these to control the cursor movements

SCROLL_STEP = 100


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
        self.window = tk.Tk()  # creating the window
        self.window.geometry(f"{WIDTH}x{HEIGHT}")
        # configuring A url input panel for the browser
        self.url_input = tk.Entry(self.window)

        # this panel will contain our canvas and scroll bar
        self.main_panel = tk.Frame(self.window)
        self.scrollbar = tk.Scrollbar(self.main_panel, orient=tk.VERTICAL)
        """ what it this object?
            - this line creates the `Canvas` inside that window:
                - self.window as an argument, so that Tk knows where to display the canvas.
                - The other arguments define the canvas’s size"""
        self.canvas = tk.Canvas(
            self.main_panel, bg="white", yscrollcommand=self.scrollbar.set
        )
        """pack is a layout manager that align Items in 4 direction
            TOP, BOTTHOM, LEFT, RIGHT.
            pack will allign based only on parent element
        """

        # will be alinged on self.window
        self.url_input.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.main_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # will be aligned on self.main_frame
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        """scrolling
            a browser lays out the page determines where everything on the page goes based
            on page coordinates.
            then rasters[draws everything] the page in terms of screen coordinates.
        """
        # The scrollbar visibility will be managed dynamically.
        self.scrollbar.config(command=self.canvas.yview)

        self.scroll = 0  # scroll buffer in order to change the view in the browser
        self.window.bind("<Down>", self.scrollDown)
        self.window.bind("<Up>", self.scrollUp)

    # Scroll cotrol
    # scrolls up
    def scrollUp(self, e):
        # Stops if the page is equal to zero
        if self.scroll == 0:
            return
        # clamp the value of scrolling to be between 0 and [itself - SCROLL_STEP]
        self.scroll = max(0, self.scroll - SCROLL_STEP)
        self.draw()
        # check if the scroll value reached the max upper level which is 0

    def scrollDown(self, e):
        # scrolls down
        max_scroll = max(0, self.max_y - HEIGHT)  # calculate the maxmux scrolable hight
        if self.scroll >= max_scroll:
            # check if the scroll value reached the max upper level which is 0
            return
        # clamb the value between the maxmun scrolable hight and current scroll value
        self.scroll = min(max_scroll, self.scroll + SCROLL_STEP)
        self.draw()

    # -----------------------------

    # page drawing and content rendering
    def draw(self):
        self.canvas.delete("all")  # to clear the old text
        # draw each character based on the stored position
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:  # skips characters below the viewing window
                continue
            if y + VSTEP < self.scroll:  # skips characters above the viewing window
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=c
            )  # The page coordinate `y` then has screen coordinate `y - self.scroll`

    # ----------------------------------

    # content loader
    def load(self, url):
        # this loads our HTML text content for now...
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        # [-1] to get the last item then [1] to access the y index of the tuple
        # this get the last index of Y
        self.max_y = self.display_list[-1][1] + VSTEP if self.display_list else 0
        self.draw()

    # this is a custom function to handle scrolling
    def update_scrollbar(self):
        # Get the actual visible height of the window/canvas
        canvas_hieght = self.canvas.winfo_height


def layout(text):
    display_text = []  # will compute and store the position of each character
    cursor_x, cursor_y = HSTEP, VSTEP  # the current cursor placement
    for c in text:
        display_text.append(
            (cursor_x, cursor_y, c)
        )  # will store the text's char coordinates in the list based on the variable

        # the movement logic
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP  # i.e Vertical steps
            cursor_x = HSTEP  # i.e Horizontical steps
    return display_text


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
