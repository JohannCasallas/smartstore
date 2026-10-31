from smartstore.cli import main


def run() -> None:
    """Punto de entrada legacy; preferir `python -m smartstore.cli`."""
    raise SystemExit(main())


if __name__ == "__main__":
    run()
