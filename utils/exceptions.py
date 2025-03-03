class InvalidRiotIDFormatError(Exception):
    """Exception for when the formatting of a Riot ID is wrong"""

    def __init__(self, message):
        super().__init__(self, message)
        self.message = message

    def __str__(self):
        return self.message
