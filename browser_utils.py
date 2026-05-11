import socket
import ssl
import tkinter as tk

# chosed because that was a common old-timey monitor size
WIDTH, HEIGHT = 900, 600
# without these vars all the text chars will be drawn in the same place,evantual overlap!
HSTEP, VSTEP = 13, 18  # these to control the cursor movements
# VSTEP IS Line Height
# HSTEP IS Char Width
SCROLL_STEP = 100

# To solve the scrollbar overlap issue we ne to add margins to the text as the following
SCROLLBAR_RESERVED = 20  # the width itself is 20 adding a padding will increase it

CONTENT_WIDTH = WIDTH - SCROLLBAR_RESERVED  # the actual possible width


class URL:
    """desc:
    A URL is composed of scheme[http,http1.1...etc], A host [like google.com]
    and lastly the path which is like "mail.google.com/mail/"

    It can also contain extra info i.e ports,queries and fragments
    """

    def __init__(self, url: str):
        # Support fallback internal schemas in order not to crash out cuz of bad input
        # or we just want to insert custom HTML pages
        if url.startswith("data:"):
            self.scheme = "data"  # its like chrome and firefox
            self.path = url.split(":", 1)[1]
            self.host = ""
            self.port = 0
            return
        # Standard network URL parsing if the user wrote (www.google.com) for example
        if "://" not in url:
            url = "http://" + url
        # getting the URL scheme
        self.scheme, url = url.split("://", 1)

        # checks for http or https scheme then idenifies the suitable port based on it
        assert self.scheme in ["http", "https"], f"Unknown Scheme {self.scheme}"
        # getting the port
        self.port = 80 if self.scheme == "http" else 443
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

    def request(self, max_redirects=5):  # Telnet IN PYTHON
        """A socket has
        - address family, which tells you how to find the other computer.
        - type, which describes the sort of conversation that’s going to happen
        - protocol, which describes the steps by which the two computers
        will establish a connection.
        """
        """Fetches the URL content with automatic redirect handling and safe socket closing."""
        if self.scheme == "data":
            return self.path
        # redirection threshold pass check
        if max_redirects <= 0:
            raise Exception("ERR_TOO_MANY_REDIRECTS: Redirect loop detected.")
        # in order to support the https we will use ssl library which handles
        #  - which encryption algorithms are user-mode
        #  - how a common encryption key is agreed to
        #  - how to make sure that the browser is connecting to the correct host.

        # we will creae context obj that will wrap the sockent itself

        # we use with keyword to auto close both the file and the socket connection
        with (
            socket.socket(
                family=socket.AF_INET,  # Address families have names that begin with `AF`
                type=socket.SOCK_STREAM,  # Types have names that begin with `SOCK`.
                proto=socket.IPPROTO_TCP,  # Protocols have names that depend on the address family.
            ) as s
        ):
            # Configure a reasonable timeout so bad links don't freeze the GUI indefinitely
            s.settimeout(5.0)
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
            # getting the respone and Wrap stream parsing safely
            # makefile is a shortcut for copying the response and pasted it into a temp file
            with s.makefile("r", encoding="utf8", newline="\r\n") as response:
                # split the response into pieces
                statusline = response.readline()
                version, status, explanation = statusline.split(" ", 2)

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
                # Handle redirection logic natively
                if status.startswith("3"):
                    new_url = response_headers.get("location")
                    if not new_url:
                        raise Exception(
                            "ERR_INVALID_REDIRECT: Server returned 3xx but no Location header."
                        )
                    # Support relative redirects
                    ifw = (
                        new_url
                        if "://" in new_url
                        else f"{self.scheme}://{self.host}{new_url}"
                    )
                    return URL(ifw).request(max_redirects - 1)

                # Headers can describe all sorts of information,
                # couple of headers are especially important because they tell us that the data
                assert "transfer-encoding" not in response_headers
                assert "content-encoding" not in response_headers
                return response.read()


class Browser:
    def __init__(self):
        self.max_y = (
            0  # Initialize max_y to prevent AttributeError before content loads
        )
        self.scroll = 0
        self.display_list = []
        # Creating the window and the canvas
        self.window = tk.Tk()  # creating the window
        self.window.geometry(f"{WIDTH}x{HEIGHT}")
        self.window.title("Custom Python Browser Engine")
        # configuring A url input panel for the browser
        self.url_input = tk.Entry(self.window)

        # this panel will contain our canvas and scroll bar
        self.main_panel = tk.Frame(self.window)

        """pack is a layout manager that align Items in 4 direction
            TOP, BOTTHOM, LEFT, RIGHT.
            pack will allign based only on parent element
        """

        # will be alinged on self.window
        self.url_input.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.main_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Had to change the Layput manager for this Frame for more robustness
        self.main_panel.columnconfigure(0, weight=1)
        self.main_panel.rowconfigure(0, weight=1)

        self.scrollbar = tk.Scrollbar(self.main_panel, orient=tk.VERTICAL)
        """ what it this object?
            - this line creates the `Canvas` inside that window:
                - self.window as an argument, so that Tk knows where to display the canvas.
                - The other arguments define the canvas’s size"""
        self.canvas = tk.Canvas(
            self.main_panel, bg="white", yscrollcommand=self.scrollbar.set
        )
        # Grid the Canvas into the expanding cell
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        # Grid the Scrollbar into the rightmost cell
        self.scrollbar.grid(
            row=0,
            column=1,
            sticky=tk.NS,
        )
        """scrolling
            a browser lays out the page determines where everything on the page goes based
            on page coordinates.
            then rasters[draws everything] the page in terms of screen coordinates.
        """
        # The scrollbar visibility will be managed dynamically.
        self.scrollbar.config(command=self.canvas.yview)

        """If we just use self.scrollUp(True) It will give AttributeError so had to
            write a callable function reference that
            accepts Tkinter's event object and routes it correctly.
            You can achieve this perfectly using a lambda function."""

        # for entering URLs
        self.window.bind("<Return>", self.handleUrl)
        # Keyboard Bindings (-1 for Up, 1 for Down)
        self.window.bind("<Up>", lambda e: self.handleScroll(e, -1, isKeyboard=True))
        self.window.bind("<Down>", lambda e: self.handleScroll(e, 1, isKeyboard=True))

        # Windows / macOS Mouse Scroll
        self.window.bind("<MouseWheel>", self._on_mousewhell)

        # Linux Mouse Scroll
        self.window.bind(
            "<Button-4>", lambda e: self.handleScroll(e, -1, isKeyboard=False)
        )
        self.window.bind(
            "<Button-5>", lambda e: self.handleScroll(e, 1, isKeyboard=False)
        )

    # ---------------------------
    # URL receiving
    # -------------------------
    def handleUrl(self, e):
        url_raw = self.url_input.get()
        self.recieved_url = URL(url_raw)
        self.load(self.recieved_url)

    # ---------------------------
    # Scroll cotrol
    # ---------------------------
    def handleScroll(self, e, direction, isKeyboard=False):
        max_scroll = max(0, self.max_y - HEIGHT)  # calculate the maxmux scrolable hight
        """since now it handle both directions at the same time it clamps
        the scroll value at two level
            - the upper level (max) which calculate the maxmum you can scroll to up
            - the bottom level (min) which calculate the minimum you can scroll to down
        the direction is responsible for idenifying weather we want to go up or down
        """
        self.scroll = max(0, min(max_scroll, self.scroll + (SCROLL_STEP * direction)))
        # call thw draw function
        self.draw()

    def _on_mousewhell(self, e):
        """desc:
        mousewhell is a sequence supported in mac and windows it depend on a delta value
        to tell where is the direction the aim of this function is to calculate the current
        scroll direction then call back the handleScroll function"""
        direction = -1 if e.delta > 0 else 1
        self.handleScroll(e, direction=direction, isKeyboard=False)

    # this is a custom function to handle scrolling
    def update_scrollbar(self):
        # Get the actual visible height of the window/canvas
        canvas_height = self.canvas.winfo_height()
        if self.max_y > canvas_height and canvas_height > 0:
            # Show scrollbar before the canvas to maintain layout order
            self.scrollbar.grid(row=0, column=1, sticky=tk.NS, padx=(10, 0))
            # 2. Synchronize the visual slider thumb with your manual self.scroll
            # Tkinter scrollbars require fractions between 0.0 and 1.0
            first_fraction = self.scroll / self.max_y
            last_fraction = (self.scroll + canvas_height) / self.max_y
            self.scrollbar.set(first_fraction, last_fraction)
        else:
            # Content fits perfectly, hide the scrollbar
            self.scrollbar.grid_remove()

    # ----------------------------------
    # page drawing and content rendering
    # ------------------------------------
    def draw(self):
        self.canvas.delete("all")  # to clear the old text
        # draw each character based on the stored position
        self.update_scrollbar()
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:  # skips characters below the viewing window
                continue
            if y + VSTEP < self.scroll:  # skips characters above the viewing window
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=c
            )  # The page coordinate `y` then has screen coordinate `y - self.scroll`

    # ---------------------
    # content loader
    # ---------------------
    def load(self, url=None):
        # this loads our HTML text content for now...
        if url is None:
            default_html = "<title>Welcome</title><h1>Engine Initialized</h1>Welcome to your custom Python browser. Please enter a destination URL above to begin navigation."
            url = URL(f"data:{default_html}")
            self.url_input.delete(0, tk.END)
            self.url_input.insert(0, "about:blank")

        # Ensure UI entry reflects actual active target
        if hasattr(url, "scheme") and url.scheme != "data":
            self.url_input.delete(0, tk.END)
            # Reconstruct clean visual address string safely
            clean_addr = f"{url.scheme}://{url.host}{url.path}"
            self.url_input.insert(0, clean_addr)

        self.scroll = 0  # Force reset top view on newly accessed pages

        # to check if the URL is correct or faulty if correct then it will continue
        try:
            body = url.request()
            text = lex(body)
        # if not then the browser will diplay a fallbaack page
        except Exception as err:
            error_html = f"<title>Navigation Error</title><h1>Failed to Connect</h1>An error occurred while attempting to reach the destination host.<br><br><b>Details:</b> {str(err)}"
            text = lex(error_html)
        self.display_list = layout(text)
        # [-1] to get the last item then [1] to access the y index of the tuple
        # this get the last index of Y
        self.max_y = int(self.display_list[-1][1] + VSTEP) if self.display_list else 0
        self.draw()


def layout(text):
    display_text = []  # will compute and store the position of each character
    cursor_x, cursor_y = HSTEP, VSTEP  # the current cursor placement
    for c in text:
        display_text.append(
            (cursor_x, cursor_y, c)
        )  # will store the text's char coordinates in the list based on the variable

        # the movement logic
        cursor_x += HSTEP
        if cursor_x >= CONTENT_WIDTH - HSTEP:
            cursor_y += VSTEP  # i.e Vertical steps
            cursor_x = HSTEP  # i.e Horizontical steps
    return display_text


def lex(body):
    in_tag = False
    text_buffer = []
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text_buffer.append(c)
    return "".join(text_buffer)
