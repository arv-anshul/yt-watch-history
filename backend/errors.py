class ENVNotFoundError(Exception):
    """Raise when environment variable not exists."""

    def __init__(self, name: str, *args: object) -> None:
        super().__init__(*args)
        self.name = name
        self.message = "Define `%s` as environment variable."

    def __str__(self) -> str:
        return self.message % self.name
