from django.utils import translation

class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ১. যদি ইউজার লগইন করা থাকে, তবে তার প্রোফাইল থেকে ভাষা নাও
        if request.user.is_authenticated:
            user_language = getattr(request.user.profile, 'language', 'en')
            translation.activate(user_language)
            request.LANGUAGE_CODE = translation.get_language()
        
        # ২. যদি ইউজার লগইন না থাকে, তবে হেডারের ভাষা নাও (Accept-Language)
        else:
            translation.activate(request.LANGUAGE_CODE)

        response = self.get_response(request)
        return response