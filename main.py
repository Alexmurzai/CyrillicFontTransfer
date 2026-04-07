"""
CyrillicFontTransfer — main.py
Точка входа в приложение.
"""

import sys
import os

# Убедимся, что корень проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import CyrillicFontTransferApp


def main():
    app = CyrillicFontTransferApp()
    app.mainloop()


if __name__ == "__main__":
    main()
