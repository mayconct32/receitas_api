from http import HTTPStatus


class DomainException(Exception):
    def __init__(self, message: str, status_code: HTTPStatus):
        self.message = message
        self.status_code = status_code
        

class ConflictingError(DomainException):
    pass


class AuthorizationError(DomainException):
    pass


#chef exceptions
class ConflictingNameError(ConflictingError):
    pass


class ConflictingEmailError(ConflictingError):
    pass


class ChefErrorNotFound(DomainException):
    pass


class AuthenticationError(DomainException):
    pass


class CredentialsError(DomainException):
    pass


#recipe exceptions
class RecipeErrorNotFound(DomainException):
    pass

