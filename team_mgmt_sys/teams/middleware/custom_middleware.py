class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to execute for each request before the view (and later middleware) are called.
        print("Custom Middleware: Before view")

        response = self.get_response(request)

        # Code to execute for each request/response after the view is called.
        print("Custom Middleware: After view")

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        print("Custom Middleware: process_view")
        # Code to execute before the view (but after any middleware).
        return None

    def process_exception(self, request, exception):
        print("Custom Middleware: process_exception")
        # Code to execute if the view raises an exception.
        return None
