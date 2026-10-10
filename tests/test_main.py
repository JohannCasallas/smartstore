from smartstore.main import main


def test_main_prints_startup_message(capsys) -> None:
    main()

    captured = capsys.readouterr()

    assert captured.out.strip() == "SmartStore: entorno inicial listo."
