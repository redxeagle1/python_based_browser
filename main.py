from browser_utils import URL, load


def main():
    import sys

    load(URL(sys.argv[1]))


if __name__ == "__main__":
    main()
