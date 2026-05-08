import tkinter

from browser_utils import URL, Browser


def main():
    import sys

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()  # to start the loop in which will update and redraw our UI


if __name__ == "__main__":
    main()
