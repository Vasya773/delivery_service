from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Customize the response format
    if response is not None:
        # Reformat Django ValidationErrors
        if isinstance(exc, DjangoValidationError):
            if hasattr(exc, "message_dict"):
                # Convert the message_dict to the desired format
                errors = {
                    field: messages for field, messages in exc.message_dict.items()
                }
            elif hasattr(exc, "messages"):
                # Handle cases where there's a single message
                errors = {"non_field_errors": exc.messages}
            else:
                errors = {"non_field_errors": [str(exc)]}

            response.data = {
                "status": "error",
                "message": "Validation error",
                "errors": errors,
            }
        else:
            response.data = {
                "status": "error",
                "message": response.data.get("detail", "An error occurred"),
                "errors": response.data,
            }
    else:
        # Handle unhandled exceptions
        response = Response(
            {"status": "error", "message": "Internal server error", "errors": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
