# coding=utf-8
from django import template
from django.contrib.auth.models import User as BaseUser
from django.utils.translation import ugettext as _
from ..models import User, FriendRequest, SocialGroup, GroupMembershipRequest
from ..utils import intmin as intmin_function

register = template.Library()


@register.filter(is_safe=False)
def intmin(value):
    """
    """
    return intmin_function(value)


def process_user_param(user):
    if not user or (isinstance(user, BaseUser) and user.is_anonymous()):
        return False
    if isinstance(user, User):
        return user
    elif isinstance(user, BaseUser):
        return User.objects.get(pk=user.pk)
    else:
        try:
            return User.objects.get(username=user)
        except:
            return False

# --------------------------------------FOLLOWER TAGS---------------------------------------------


@register.filter
def followed_by(user1, user2):
    """
    Returns whether user1 is followed by user2 or not.
    """
    user1 = process_user_param(user1)
    user2 = process_user_param(user2)
    if not user1 or not user2:
        return False
    return user1.followed_by(user2)


@register.filter
def is_follower_of(user1, user2):
    """
    Returns whether user1 follows user2 or not.

    :param user1: An User instance.
    :param user2: An User instance.

    """
    user1 = process_user_param(user1)
    user2 = process_user_param(user2)
    if not user1 or not user2:
        return False
    return user2.followed_by(user1)


@register.filter
def followers_count(user):
    """
    Returns user followers count
    :param user: An User instance
    """
    user = process_user_param(user)
    if not user:
        return 0
    return user.followers()


@register.filter
def followed_count(user):
    """
    Returns the count of how many users is the user following
    :param user: An User instance
    """
    user = process_user_param(user)
    if not user:
        return 0
    return user.following()

# --------------------------------------FRIENDSHIP TAGS-------------------------------------------


@register.filter
def is_friends_with(user1, user2):
    """
    Returns whether user1 and user2 are friends or not.

    :param user1: An User instance.
    :param user2: An User instance.

    """
    user1 = process_user_param(user1)
    user2 = process_user_param(user2)
    if not user1 or not user2:
        return False
    return user1.friend_of(user2)


@register.filter
def has_requested_friendship_to(user1, user2):
    """
    Returns True if user1 has requested friendship to user2, False otherwise.

    :param user1: An User instance.
    :param user2: An User instance.

    """
    user1 = process_user_param(user1)
    user2 = process_user_param(user2)
    if not user1 or not user2 or user1 == user2:
        return False
    return FriendRequest.objects.filter(from_user=user1, to_user=user2, accepted=False).exists()


@register.filter
def friends_count(user):
    """
    Returns how many users have a "friendship" relationship with given user

    :param user: An User instance.

    """
    user_obj = process_user_param(user)
    if not user_obj:
        return 0
    return user_obj.friends()

# --------------------------------------GROUPS TAGS-------------------------------------------


def process_group_param(group):
    if not group:
        return False
    if isinstance(group, SocialGroup):
        return group
    else:
        try:
            return SocialGroup.objects.get(slug=group)
        except:
            return False


role_dict = {
    'creator': _(u"Creator"),
    'admin': _(u"Administrator"),
    'member': _(u"Member")
}


@register.filter
def relationship_with(group, user):
    """
    Returns relationship between group and passed user

    :param group: A SocialGroup instance.
    :param user: An User instance.

    """
    user_obj = process_user_param(user)
    group_obj = process_group_param(group)
    if not user_obj or not group_obj:
        return None
    return role_dict[group_obj.relationship_with(user_obj)[1]]


@register.assignment_tag
def has_creator(group, user):
    """
    Returns True if user is the creator, False otherwise

    :param user: An User instance.
    :param group: A SocialGroup instance.

    """
    user_obj = process_user_param(user)
    group_obj = process_group_param(group)
    if not user_obj or not group_obj:
        return False
    return group_obj.creator == user_obj


@register.assignment_tag
def has_admin(group, user):
    """
    Returns True if user is in the group list of administrators or is the creator, False otherwise

    :param user: An User instance.
    :param group: A SocialGroup instance.

    """
    user_obj = process_user_param(user)
    group_obj = process_group_param(group)
    if not user_obj or not group_obj:
        return False
    return group_obj.has_admin(user_obj)


@register.assignment_tag
def is_group_member(user, group):
    """
    Returns True if user is in a group member, False otherwise

    :param user: An User instance.
    :param group: A SocialGroup instance.

    """
    user_obj = process_user_param(user)
    group_obj = process_group_param(group)
    if not user_obj or not group_obj:
        return False
    return group_obj.has_member(user_obj)


@register.assignment_tag
def has_requested_membership(user, group):
    """
    Returns True if user1 has requested friendship to user2, False otherwise.

    :param user: An User instance.
    :param group: An SocialGroup instance.

    """
    user_obj = process_user_param(user)
    group_obj = process_group_param(group)
    if not user_obj or not group_obj:
        return False
    return GroupMembershipRequest.objects.filter(
        requester=user_obj,
        group=group_obj,
        accepted=False,
        denied=False
    ).exists()


@register.simple_tag()
def render_user_rol(user, group):
    return role_dict[group.member_role_list[user.pk]]


@register.filter
def groups_count(user):
    """
    Returns the total count of how many groups the user is a member of
    """
    user_obj = process_user_param(user)
    if not user_obj:
        return 0
    return user_obj.social_groups()
