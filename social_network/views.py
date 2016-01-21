# coding=utf-8
import json
import logging
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView, View, DetailView, TemplateView, UpdateView
from . import SERVER_SUCCESS_MESSAGE
from utils import intmin
from models import User, FriendRequest, SocialGroup, GroupMembershipRequest
from forms import (
    FriendRequestForm,
    SocialGroupForm,
    GroupCommentForm,
    GroupMembershipRequestForm,
    GroupPhotoForm,
    ProfileCommentForm,
    GroupSharedLinkForm
)

logger = logging.getLogger(__name__)


class JSONResponseEnabledMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    json_response_class = HttpResponse
    json_enabled_methods = ['post']

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.json_enabled_methods:
            self.json_enabled = True
        else:
            self.json_enabled = False
        return super(JSONResponseEnabledMixin, self).dispatch(request, *args, **kwargs)

    def render_to_json(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        response_kwargs['content_type'] = 'application/json'
        return self.json_response_class(
            json.dumps(context),
            **response_kwargs
        )

    def render_to_response(self, context, **response_kwargs):
        if self.json_enabled:
            return self.render_to_json(context, **response_kwargs)
        else:
            return super(JSONResponseEnabledMixin, self).render_to_response(context, **response_kwargs)


class BaseFriendRequestCreateView(CreateView):
    form_class = FriendRequestForm
    template_name = 'social_network/friend/request.html'

    def get_form_kwargs(self):
        kwargs = super(BaseFriendRequestCreateView, self).get_form_kwargs()
        kwargs['initial'] = {
            'from_user': self.request.user,
            'to_user': User.objects.get(username=self.kwargs['username']),
        }
        return kwargs


class FriendRequestCreateView(JSONResponseEnabledMixin, BaseFriendRequestCreateView):

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_json({
            'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
        }, status=201)


class FriendRequestListView(ListView):
    template_name = 'social_network/friend/list.html'

    def get_queryset(self):
        self.queryset = self.request.user.user_incoming_friend_requests.filter(accepted=False)
        return super(FriendRequestListView, self).get_queryset()


class AcceptFriendRequestView(JSONResponseEnabledMixin, View):

    def post(self, request, *args, **kwargs):
        try:
            result = FriendRequest.objects.get(pk=kwargs['pk']).accept(self.request.user)
            if not result:
                return HttpResponseForbidden()
            return self.render_to_json({
                'result': result,
                'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
            })
        except FriendRequest.DoesNotExist:
            return HttpResponseBadRequest()
        except Exception:
            return HttpResponseServerError()


class DenyFriendRequestView(JSONResponseEnabledMixin, View):

    def post(self, request, *args, **kwargs):
        try:
            result = FriendRequest.objects.get(pk=kwargs['pk']).deny(self.request.user)
            if not result:
                return HttpResponseForbidden()
            return self.render_to_json({
                'result': result,
                'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
            })
        except FriendRequest.DoesNotExist:
            return HttpResponseBadRequest()
        except Exception:
            return HttpResponseServerError()


class FriendshipButtonsTemplateView(TemplateView):
    template_name = 'social_network/buttons/_friendship_buttons.html'

    def get_context_data(self, **kwargs):
        context = super(FriendshipButtonsTemplateView, self).get_context_data(**kwargs)
        context.update({
            'target_user': User.objects.get(username=self.kwargs['username'])
        })
        return context


class FollowerRelationshipToggleView(JSONResponseEnabledMixin, View):

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(username=kwargs['username'])

            if user.followed_by(request.user):
                request.user.stop_following(user)
                tooltip = _(u"Follow")
                toggle_status = False
            else:
                request.user.follow(user)
                tooltip = _(u"Stop Following")
                toggle_status = True

            followers = user.followers()

            return self.render_to_json({
                'result': True,
                'toggle_status': toggle_status,
                'counter': followers,
                'counterStr': intmin(followers),
                'tooltip': force_text(tooltip)
            })

        except Exception as e:
            logger.exception(e)
            return self.render_to_json({'result': False})


class FollowerRelationshipCreateView(JSONResponseEnabledMixin, View):

    def post(self, request, *args, **kwargs):
        try:
            request.user.follow(User.objects.get(username=kwargs['username']))
            return self.render_to_json({
                'result': True,
                'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
            }, status=201)
        except User.DoesNotExist:
            return HttpResponseBadRequest()


class FollowerRelationshipDestroyView(JSONResponseEnabledMixin, View):

    def post(self, request, *args, **kwargs):
        try:
            request.user.stop_following(User.objects.get(username=kwargs['username']))
            return self.render_to_json({
                'result': True,
                'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
            })
        except User.DoesNotExist:
            return HttpResponseBadRequest()


class UserSocialGroupList(ListView):
    template_name = 'social_network/group/list.html'

    def get_queryset(self):
        self.queryset = SocialGroup.on_site.integrated_by(self.request.user)
        return super(UserSocialGroupList, self).get_queryset()


class BaseProfileCommentCreateView(CreateView):
    template_name = 'social_network/userfeed/comment.html'
    form_class = ProfileCommentForm

    def get_form_kwargs(self):
        kwargs = super(BaseProfileCommentCreateView, self).get_form_kwargs()
        kwargs['initial'] = {
            'receiver': User.objects.get(username=self.kwargs['username']),
            'creator': self.request.user
        }
        return kwargs


class ProfileCommentCreateView(JSONResponseEnabledMixin, BaseProfileCommentCreateView):

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_json({
            'result': True,
            'comment_id': self.object.pk,
            'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
        }, status=201)


class SocialGroupListView(ListView):
    template_name = 'social_network/group/detail/members.html'
    paginate_by = 10

    def get_queryset(self):
        self.queryset = SocialGroup.on_site.all()
        return super(SocialGroupListView, self).get_queryset()


class BaseSocialGroupCreateView(CreateView):
    form_class = SocialGroupForm
    template_name = 'social_network/group/form.html'

    def get_form_kwargs(self):
        kwargs = super(BaseSocialGroupCreateView, self).get_form_kwargs()
        kwargs['initial'] = {
            'creator': self.request.user,
            'site': Site.objects.get_current()
        }
        return kwargs


class SocialGroupCreateView(JSONResponseEnabledMixin, BaseSocialGroupCreateView):

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_json({
            'result': True,
            'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
        }, status=201)


class BaseSocialGroupUpdateView(UpdateView):
    queryset = SocialGroup.on_site.all()
    form_class = SocialGroupForm
    template_name = 'social_network/group/form.html'

    def get_form_kwargs(self):
        kwargs = super(BaseSocialGroupUpdateView, self).get_form_kwargs()
        kwargs['initial'] = {
            'creator': self.request.user,
            'site': Site.objects.get_current()
        }
        return kwargs


class SocialGroupUpdateView(JSONResponseEnabledMixin, BaseSocialGroupUpdateView):

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_json({
            'result': True,
            'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
        }, status=201)


class SocialGroupDetailView(DetailView):
    model = SocialGroup
    template_name = 'social_network/group/detail/main.html'
    context_object_name = 'group'


class BaseSocialGroupRequestCreateView(CreateView):
    form_class = GroupMembershipRequestForm
    template_name = 'social_network/group/request.html'

    def get_form_kwargs(self):
        kwargs = super(BaseSocialGroupRequestCreateView, self).get_form_kwargs()
        kwargs['initial'] = {
            'requester': self.request.user,
            'group': SocialGroup.objects.get(slug=self.kwargs['slug'])
        }
        return kwargs


class SocialGroupRequestCreateView(JSONResponseEnabledMixin, BaseSocialGroupRequestCreateView):

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_json({
            'result': True,
            'successMsg': force_text(SERVER_SUCCESS_MESSAGE),
            'sentLabel': force_text(_(u"Request Sent"))
        }, status=201)


class SocialGroupRequestAcceptView(JSONResponseEnabledMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            result = GroupMembershipRequest.objects.get(
                pk=kwargs['pk'], group__slug=kwargs['slug']
            ).accept(self.request.user)
            if not result:
                return HttpResponseForbidden()
            return self.render_to_json({
                'result': result,
                'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
            })
        except GroupMembershipRequest.DoesNotExist:
            return HttpResponseBadRequest()
        except Exception:
            return HttpResponseServerError()


class SocialGroupRequestDenyView(JSONResponseEnabledMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            result = GroupMembershipRequest.objects.get(
                pk=kwargs['pk'], group__slug=kwargs['slug']
            ).deny(self.request.user)
            if not result:
                return HttpResponseForbidden()
            return self.render_to_json({
                'result': result,
                'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
            })
        except GroupMembershipRequest.DoesNotExist:
            return HttpResponseBadRequest()
        except Exception:
            return HttpResponseServerError()


class SocialGroupJoinView(JSONResponseEnabledMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            result = self.request.user.join(SocialGroup.objects.get(slug=kwargs['slug']))
            if not result:
                return HttpResponseForbidden()
            return self.render_to_json({
                'result': result,
                'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
            })
        except SocialGroup.DoesNotExist:
            return HttpResponseBadRequest()
        except Exception:
            return HttpResponseServerError()


class BaseGroupPostCreateView(CreateView):

    def get_form_kwargs(self):
        kwargs = super(BaseGroupPostCreateView, self).get_form_kwargs()
        kwargs['initial'] = {
            'creator': self.request.user,
            'group': SocialGroup.objects.get(slug=self.kwargs['slug']),
        }
        return kwargs


class GroupPostCreateView(JSONResponseEnabledMixin):

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_json({
            'result': True,
            'successMsg': force_text(SERVER_SUCCESS_MESSAGE)
        }, status=201)


class BaseGroupCommentCreateView(BaseGroupPostCreateView):
    form_class = GroupCommentForm
    template_name = 'social_network/group/comment.html'


class GroupCommentCreateView(GroupPostCreateView, BaseGroupCommentCreateView):
    pass


class BaseGroupLinkCreateView(BaseGroupPostCreateView):
    form_class = GroupSharedLinkForm
    template_name = 'social_network/group/link.html'


class GroupLinkCreateView(GroupPostCreateView, BaseGroupLinkCreateView):
    pass


class BaseGroupPhotoCreateView(BaseGroupPostCreateView):
    form_class = GroupPhotoForm
    template_name = 'social_network/group/photo.html'


class GroupPhotoCreateView(GroupPostCreateView, BaseGroupPhotoCreateView):
    pass


class SocialGroupFeedView(ListView):
    template_name = 'social_network/group/detail/feed.html'

    def get_queryset(self):
        self.group = SocialGroup.on_site.filter(slug=self.kwargs.get('slug'))
        self.queryset = self.group.feed_items.all()
        return super(SocialGroupFeedView, self).get_queryset()


class SocialGroupMembershipRequestsList(ListView):
    template_name = 'social_network/group/detail/requests.html'

    def get_queryset(self):
        self.queryset = GroupMembershipRequest.objects.filter(
            group__slug=self.kwargs['slug'],
            accepted=False,
            denied=False
        )
        return super(SocialGroupMembershipRequestsList, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(SocialGroupMembershipRequestsList, self).get_context_data(**kwargs)
        context['group'] = self.kwargs['slug']
        return context


class SocialGroupMembersList(ListView):
    template_name = 'social_network/group/detail/members.html'

    def get_queryset(self):
        self.group = SocialGroup.objects.get(slug=self.kwargs['slug'])
        self.queryset = User.objects.filter(pk__in=[user.pk for user in self.group.member_list])
        return super(SocialGroupMembersList, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(SocialGroupMembersList, self).get_context_data(**kwargs)
        context.update({
            'group': SocialGroup.objects.get(slug=self.kwargs['slug'])
        })
        return context


class MembershipButtonsTemplateView(TemplateView):
    template_name = 'social_network/buttons/_membership_buttons.html'

    def get_context_data(self, **kwargs):
        context = super(MembershipButtonsTemplateView, self).get_context_data(**kwargs)
        context.update({
            'group': SocialGroup.objects.get(slug=self.kwargs['slug'])
        })
        return context

