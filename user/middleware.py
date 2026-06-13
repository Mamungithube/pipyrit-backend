from django.utils import translation

class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_language = getattr(request.user.profile, 'language', 'en')
            translation.activate(user_language)
            request.LANGUAGE_CODE = translation.get_language()
        
        else:
            translation.activate(request.LANGUAGE_CODE)

        response = self.get_response(request)
        return response