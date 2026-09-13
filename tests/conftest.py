def pytest_addoption(parser):
    parser.addoption(
        "--update-expected",
        action="store_true",
        default=False,
        help="Rewrite the expected Mapfiles instead of comparing against them",
    )
