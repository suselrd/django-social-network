# coding=utf-8
from django import forms
from django.core.exceptions import ValidationError
from models import (
    User,
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
