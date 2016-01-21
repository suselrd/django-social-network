# coding=utf-8
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required as lr
import views

relationship_patterns = patterns(
    '',
    url(
        r'^friend_requests/$',
        lr(views.FriendRequestListView.as_view()),
        name='friend_requests'
    ),

    url(
        r'^friend_requests/(?P<pk>\d+)/accept/$',
        lr(views.AcceptFriendRequestView.as_view()),
        name='accept_friend_request'
    ),

    url(
        r'^friend_requests/(?P<pk>\d+)/deny/$',
        lr(views.DenyFriendRequestView.as_view()),
        name='deny_friend_request'
    ),

    url(
        r'^(?P<username>\w+)/toggle_follow/$',
        lr(views.FollowerRelationshipToggleView.as_view()),
        name="toggle_follow"
    ),

    url(
        r'^(?P<username>\w+)/follow/$',
        lr(views.FollowerRelationshipCreateView.as_view()),
        name="follow"
    ),

    url(
        r'^(?P<username>\w+)/unfollow/$',
        lr(views.FollowerRelationshipDestroyView.as_view()),
        name="unfollow"
    ),
    
    url(
        r'^(?P<username>\w+)/buttons/$',
        lr(views.FriendshipButtonsTemplateView.as_view()),
        name='friendship_buttons'
    ),

    url(
        r'^(?P<username>\w+)/request_friendship/$',
        lr(views.BaseFriendRequestCreateView.as_view()),
        name='request_friendship'
    ),

    url(
        r'^(?P<username>\w+)/request_friendship_inline/$',
        lr(views.FriendRequestCreateView.as_view()),
        name='request_friendship_inline'
    ),

    url(
        r'^(?P<username>\w+)/groups/$',
        views.UserSocialGroupList.as_view(),
        name='groups'
    ),

    url(
        r'^(?P<username>\w+)/comment/$',
        lr(views.BaseProfileCommentCreateView.as_view()),
        name="profile_comment"
    ),

    url(
        r'^(?P<username>\w+)/comment_inline/$',
        lr(views.ProfileCommentCreateView.as_view()),
        name="profile_comment_inline"
    ),

)

group_patterns = patterns(
    '',
    url(
        r'^$',
        views.SocialGroupListView.as_view(),
        name='all'
    ),

    url(
        r'^new/$',
        lr(views.BaseSocialGroupCreateView.as_view()),
        name='new'
    ),

    url(
        r'^new_inline/$',
        lr(views.SocialGroupCreateView.as_view()),
        name='new_inline'
    ),

    url(
        r'^(?P<slug>[\w-]+)/$',
        views.SocialGroupDetailView.as_view(),
        name='details'
    ),

    url(
        r'^(?P<slug>[\w-]+)/members/$',
        views.SocialGroupMembersList.as_view(),
        name='members'
    ),

    url(
        r'^(?P<slug>[\w-]+)/feed/$',
        views.SocialGroupFeedView.as_view(),
        name='feed'
    ),

    url(
        r'^(?P<slug>[\w-]+)/requests/$',
        lr(views.SocialGroupMembershipRequestsList.as_view()),
        name='requests'
    ),

    url(
        r'^(?P<slug>[\w-]+)/buttons/$',
        lr(views.MembershipButtonsTemplateView.as_view()),
        name='membership_buttons'
    ),

    url(
        r'^(?P<slug>[\w-]+)/edit/$',
        lr(views.BaseSocialGroupUpdateView.as_view()),
        name='edit'
    ),

    url(
        r'^(?P<slug>[\w-]+)/edit_inline/$',
        lr(views.SocialGroupUpdateView.as_view()),
        name='edit_inline'
    ),

    url(
        r'^(?P<slug>[\w-]+)/comment/$',
        lr(views.BaseGroupCommentCreateView.as_view()),
        name='comment'
    ),

    url(
        r'^(?P<slug>[\w-]+)/comment_inline/$',
        lr(views.GroupCommentCreateView.as_view()),
        name='comment_inline'
    ),

    url(
        r'^(?P<slug>[\w-]+)/post_link/$',
        lr(views.BaseGroupLinkCreateView.as_view()),
        name='post_link'
    ),

    url(
        r'^(?P<slug>[\w-]+)/post_link_inline/$',
        lr(views.GroupLinkCreateView.as_view()),
        name='post_link_inline'
    ),

    url(
        r'^(?P<slug>[\w-]+)/post_photo/$',
        lr(views.BaseGroupPhotoCreateView.as_view()),
        name='post_photo'
    ),

    url(
        r'^(?P<slug>[\w-]+)/post_photo_inline/$',
        lr(views.GroupPhotoCreateView.as_view()),
        name='post_photo_inline'
    ),

    url(
        r'^(?P<slug>[\w-]+)/join/$',
        lr(views.SocialGroupJoinView.as_view()),
        name='join'
    ),

    url(
        r'^(?P<slug>[\w-]+)/request_membership/$',
        lr(views.BaseSocialGroupRequestCreateView.as_view()),
        name='request_membership'
    ),

    url(
        r'^(?P<slug>[\w-]+)/request_membership_inline/$',
        lr(views.SocialGroupRequestCreateView.as_view()),
        name='request_membership_inline'
    ),

    url(
        r'^(?P<slug>[\w-]+)/requests/(?P<pk>\d+)/accept/$',
        lr(views.SocialGroupRequestAcceptView.as_view()),
        name='accept_request'
    ),

    url(
        r'^(?P<slug>[\w-]+)/requests/(?P<pk>\d+)/deny/$',
        lr(views.SocialGroupRequestDenyView.as_view()),
        name='deny_request'
    ),

)

urlpatterns = patterns(
    '',
    url(
        r'^group/', include(group_patterns, namespace='group')
    ),

    url(
        r'^', include(relationship_patterns, namespace='user')
    ),
)
