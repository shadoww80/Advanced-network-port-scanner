"""Application entry point."""

from portscanner.logging_config import get_logger, setup_logging
from portscanner.ui.app import PortScannerApp

logger = get_logger("main")


def main() -> None:
    setup_logging()
    logger.info("Application startup")

    app = PortScannerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
