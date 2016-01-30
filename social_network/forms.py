# coding=utf-8
import json
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms.util import ErrorList
from models import (
    FriendRequest,
    SocialGroup, 
    GroupPost,
    GroupMembershipRequest, 
    FeedComment,
)


class FriendRequestForm(forms.ModelForm):

    class Meta:
        model = FriendRequest
        fields = ('from_user', 'to_user', 'message')
        widgets = {
            'from_user': forms.widgets.HiddenInput,
            'to_user': forms.widgets.HiddenInput,
        }


class ProfileCommentForm(forms.ModelForm):
    class Meta:
        model = FeedComment
        fields = ('creator', 'receiver', 'comment')
        widgets = {
            'creator': forms.widgets.HiddenInput,
            'receiver': forms.widgets.HiddenInput,
        }


class SocialGroupForm(forms.ModelForm):
    administrators = forms.ModelMultipleChoiceField(User.objects.all(), required=False)

    class Meta:
        model = SocialGroup
        fields = ('creator', 'name', 'description', 'closed', 'administrators', 'site', 'image')
        widgets = {
            'creator': forms.widgets.HiddenInput,
            'site': forms.widgets.HiddenInput
        }


class GroupPostForm(forms.ModelForm):

    class Meta(object):
        model = GroupPost
        widgets = {
            'creator': forms.widgets.HiddenInput,
            'group': forms.widgets.HiddenInput
        }

    def clean(self):
        if not self.cleaned_data['group'].has_member(self.cleaned_data['creator']):
            raise ValidationError("Only members can post in groups")
        return self.cleaned_data


class GenericGroupPostForm(GroupPostForm):

    class Meta(GroupPostForm.Meta):
        fields = ('creator', 'group', 'comment', 'url', 'image')

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, instance=None):
        super(GroupPostForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix,
                                            empty_permitted, instance)
        if self.instance and self.instance.url != '':
            if not self.instance.url.startswith('http://') and not self.instance.url.startswith('https://'):
                self.initial['url'] = 'http://%s%s' % (Site.objects.get_current().domain, self.instance.url)


class GroupCommentForm(GroupPostForm):

    class Meta(GroupPostForm.Meta):
        fields = ('creator', 'group', 'comment',)


class GroupSharedLinkForm(GroupPostForm):
    class Meta(GroupPostForm.Meta):
        fields = ('creator', 'group', 'url', 'comment',)


class GroupPhotoForm(GroupPostForm):

    class Meta(GroupPostForm.Meta):
        fields = ('creator', 'group', 'image', 'comment',)


class GroupMembershipRequestForm(forms.ModelForm):
    class Meta:
        model = GroupMembershipRequest
        fields = ('requester', 'group', 'message')
        widgets = {
            'requester': forms.widgets.HiddenInput,
            'group': forms.widgets.HiddenInput
        }

    def clean(self):
        if GroupMembershipRequest.objects.filter(
            requester=self.cleaned_data['requester'],
            group=self.cleaned_data['group'],
            accepted=False,
            denied=False,
        ).exists():
            raise ValidationError('Pre-existing group membership request from this user to this group.')
        return self.cleaned_data


class ShareSocialGroupForm(forms.ModelForm):
    content_type = forms.ModelChoiceField(ContentType.objects.all(), widget=forms.HiddenInput(), required=False)
    object_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    groups = forms.MultipleChoiceField(
        choices=[],
        required=False,
        label=_(u'Social Groups'),
        help_text=_(u"Select Social Groups")
    )
    comment = forms.CharField(
        max_length=500, widget=forms.Textarea(attrs={'rows': 2}), required=False,
        help_text=_(u"Share something with friends and groups.")
    )

    class Meta:
        model = GroupPost
        fields = ('creator',)
        widgets = {
            'creator': forms.widgets.HiddenInput,
        }

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False):
        super(ShareSocialGroupForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix,
                                                   empty_permitted)
        if initial:
            if 'groups' in initial and initial['groups'] and isinstance(initial['groups'], (list, set, tuple)):
                self.initial['groups'] = [group.pk for group in initial['groups']]

            if 'creator' not in initial or not initial['creator']:
                raise ImproperlyConfigured("The creator must be defined in the initial content.")

            self.fields['groups'].choices = [(group.pk, group.name) for group in initial['creator'].social_group_list()]

        if data:
            creator_key = self.prefix + '-creator' if self.prefix else 'creator'
            if data[creator_key]:
                self.fields['groups'].choices = [(group.pk, group.name) for group in User.objects.get(pk=data[creator_key]).social_group_list()]

    def clean(self):
        cleaned_data = super(ShareSocialGroupForm, self).clean()
        if ('comment' in cleaned_data and (not cleaned_data['comment'] or cleaned_data['comment'] == "")) and cleaned_data['groups']:
            self._errors['groups'] = self.error_class(
                [_(u"You must type a comment to post in your social groups.")]
            )

        if cleaned_data['content_type'] and cleaned_data['object_pk']:
            self.content_object = cleaned_data['content_type'].get_object_for_this_type(pk=cleaned_data['object_pk'])

        return cleaned_data

    def save(self, commit=True, content_object=None):
        comment = self.cleaned_data.get('comment', None)
        groups = self.cleaned_data.get('groups', None)
        content_object = content_object or self.content_object
        if comment and comment != "" and groups and groups and content_object and commit:
            group_posts = []
            for group in groups:
                url = content_object.get_absolute_url() if getattr(content_object, 'get_absolute_url', False) else content_object.get_url()
                group_post = GroupPost.objects.create(
                    creator=self.cleaned_data['creator'],
                    group=SocialGroup.objects.get(pk=group),
                    comment=comment,
                    url=url,
                    image=content_object.get_picture(),
                )
                group_posts.append(group_post)
            return group_posts
        return None