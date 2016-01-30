# coding=utf-8
from content_interactions.mixins import ContentInteractionMixin


class ShareToSocialGroupTargetMixin(ContentInteractionMixin):

    def get_picture(self):
        picture = getattr(self, 'picture', None)
        return picture() if callable(picture) else picture

    def get_url(self):
        url = getattr(self, 'url', "")
        return url() if callable(url) else url