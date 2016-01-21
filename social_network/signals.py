# coding=utf-8
from django.dispatch import Signal

friend_request_created = Signal(providing_args=['instance', 'user', 'receiver'])
friendship_created = Signal(providing_args=['friend', 'user'])

follower_relationship_created = Signal(providing_args=['followed', 'user'])
follower_relationship_destroyed = Signal(providing_args=['followed', 'user'])

social_group_created = Signal(providing_args=['instance', 'user'])
social_group_post_created = Signal(providing_args=['instance', 'user'])
social_group_membership_request_created = Signal(providing_args=['instance', 'user', 'group'])
social_group_member_added = Signal(providing_args=['group', 'member', 'user'])

profile_comment_created = Signal(providing_args=['instance', 'user'])

