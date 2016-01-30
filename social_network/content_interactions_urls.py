# coding=utf-8
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required as lr
from content_interactions.urls import urlpatterns
import views


urlpatterns = patterns(
    '',
    url(
        r'^(?P<content_type_pk>\d+)-(?P<object_pk>\d+)/share/$',
        lr(views.ShareView.as_view()),
        name="share_item"
    ),
) + urlpatterns
