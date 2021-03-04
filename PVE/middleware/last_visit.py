from django.core.cache import cache
from django.utils import timezone
from users.models import CustomUser

# other user model import


def last_visit_middleware(get_response):
    def middleware(request):
        """
        Save the time of last user visit
        """
        response = get_response(request)

        if request.session.session_key:
            key = "recently-seen-{}".format(request.session.session_key)
            recently_seen = cache.get(key)

            # is_authenticated hits db as it selects user row
            # so we will hit it only if user is not recently seen
            if not recently_seen and request.user.is_authenticated:
                CustomUser.objects.filter(id=request.user.id).update(
                    last_visit=timezone.now()
                )

                visit_time = 60 * 30  # 30 minutes
                cache.set(key, 1, visit_time)

        return response

    return middleware
