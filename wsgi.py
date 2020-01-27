#!/usr/bin/env python
from uhs12app import create_app
import argparse

app = create_app()

if __name__ == "__main__":
    app.run()

