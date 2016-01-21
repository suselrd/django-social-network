# coding=utf-8'


class SocialMiddleware(object):
    def process_request(self, request):
        assert hasattr(
            request, 'user'
        ), "The social middleware requires authentication middleware to be installed. " \
           "Edit your MIDDLEWARE_CLASSES setting to insert 'social_network.middleware.SocialMiddleware'."
        from social_network.models import User
        if not request.user.is_anonymous():
            request.user = User.objects.get(pk=request.user.pk)
