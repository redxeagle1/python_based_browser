import tkinter

from browser_utils import Browser


def main():
    browser = Browser()
    browser.load()
    tkinter.mainloop()  # to start the loop in which will update and redraw our UI


if __name__ == "__main__":
    main()
