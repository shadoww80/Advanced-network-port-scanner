"""Module entry point: ``python -m portscanner``."""

from portscanner import PortScannerApp
from portscanner.logging_config import get_logger, setup_logging

logger = get_logger("__main__")


def main() -> None:
    setup_logging()
    logger.info("Application startup")

    app = PortScannerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
