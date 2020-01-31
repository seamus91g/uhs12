#!/usr/bin/env python
from uhs12app import create_app
import argparse

app = create_app()

def main():
    parser = argparse.ArgumentParser(description='Input params')
    parser.add_argument('-d', '--debug', action='store_true', default=False, help='Run in debug mode')
    parser.add_argument('-l', '--live', action='store_true', default=False, help='Use host 0.0.0.0')
    parser.add_argument('-p', '--port', default=5000, help='Choose a port. Default is 5000')
    args = parser.parse_args()
    hostip = '0.0.0.0' if args.live else None

    app.run(host=hostip, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
