from frontend.ui import MainWindow
from frontend.core import Core
from PyQt5.QtWidgets import QApplication
import sys
import argparse


def main():

    core = Core()
    core.main()


if __name__ == "__main__":
    main()
