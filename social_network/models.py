# coding: utf-8
from django.contrib.auth import get_user_model
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from social_graph import Graph
from notifications.models import Event, NotificationTemplateConfig
from signals import (
    follower_relationship_created,
    follower_relationship_destroyed,
    friend_request_created,
    friendship_created,
    social_group_created,
    social_group_membership_request_created,
    social_group_member_added,
    social_group_post_created,
    profile_comment_created,
)
from utils import (
    followed_by_edge,
    follower_of_edge,
    friendship_edge,
    integrated_by_edge,
    member_of_edge,
    generate_sha1,
    group_post_event_type
)

BaseUser = get_user_model()
BaseManager = BaseUser._default_manager.__class__
graph = Graph()


class UserManager(BaseManager):

    def followed_by_users(self, user):
        follower_of = follower_of_edge()
        count = graph.edge_count(user, follower_of)
        ids = [node.pk for node, attributes, time in graph.edge_range(user, follower_of, 0, count)]
        return self.get_queryset().filter(pk__in=ids)

    def members_of(self, group):
        integrated_by = integrated_by_edge()
        count = graph.edge_count(group, integrated_by)
        ids = [node.pk for node, attributes, time in graph.edge_range(group, integrated_by, 0, count)]
        return self.get_queryset().filter(pk__in=ids)


class User(BaseUser):
    objects = UserManager()

    class Meta:
        proxy = True

    @models.permalink
    def get_request_friendship_url(self):
        return 'user:request_friendship', [self.username]

    def get_site(self):
        return Site.objects.get_current()

    def followers(self):
        return graph.edge_count(self, followed_by_edge(), self.get_site())

    def follower_list(self):
        count = self.followers()
        return [node for node, attributes, time in graph.edge_range(self, followed_by_edge(), 0, count, self.get_site())]

    def following(self):
        return graph.edge_count(self, follower_of_edge(), self.get_site())

    def following_list(self):
        count = self.following()
        return [node for node, attributes, time in graph.edge_range(self, follower_of_edge(), 0, count, self.get_site())]

    def followed_by(self, user):
        return graph.edge_get(self, followed_by_edge(), user, self.get_site()) is not None

    def follow(self, user):
        _edge = graph.edge(self, user, follower_of_edge(), self.get_site(), {})
        if _edge:
            follower_relationship_created.send(sender=self.__class__, followed=user, user=self)
        return _edge

    def stop_following(self, user):
        _deleted = graph.no_edge(self, user, follower_of_edge(), self.get_site())
        if _deleted:
            follower_relationship_destroyed.send(sender=self.__class__, followed=user, user=self)
        return _deleted

    def friend_of(self, user):
        return graph.edge_get(self, friendship_edge(), user, self.get_site()) is not None

    def friends(self):
        return graph.edge_count(self, friendship_edge(), self.get_site())

    def friend_list(self):
        return [node for node, attributes, time in graph.edge_range(self, friendship_edge(), self.get_site())]

    def make_friend_of(self, user):
        _edge = graph.edge(self, user, friendship_edge(), self.get_site(), {})
        if _edge:
            friendship_created.send(sender=self.__class__, friend=user, user=self)
        return _edge

    def social_groups(self):
        return graph.edge_count(self, member_of_edge(), self.get_site())

    def social_group_list(self):
        count = self.social_groups()
        return [group for group, attributes, time in graph.edge_range(self, member_of_edge(), 0, count, self.get_site())]

    def specific_role_social_group_list(self, role):
        count = self.social_groups()
        return [group for group, attributes, time in graph.edge_range(self, member_of_edge(), 0, count, self.get_site())
                if attributes['role'] == role]

    def is_member_of(self, group):
        return graph.edge_get(group, integrated_by_edge(), self, group.site) is not None

    def is_admin_of(self, group):
        return self in group.administrators.all()

    def is_creator_of(self, group):
        return self == group.creator

    def join(self, group):
        return group.add_member(self)


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='user_outgoing_friend_requests', verbose_name=_(u'requester'))
    to_user = models.ForeignKey(User, related_name='user_incoming_friend_requests', verbose_name=_(u'receiver'))
    message = models.TextField(blank=True, verbose_name=_(u'message'))
    accepted = models.BooleanField(default=False, verbose_name=_(u'accepted'), blank=True)
    denied = models.BooleanField(default=False, verbose_name=_(u'denied'), blank=True)

    class Meta:
        verbose_name = _(u'friend request')
        verbose_name_plural = _(u'friend requests')

    def __unicode__(self):
        return u"%s" % self.to_user.get_full_name() or self.to_user.get_username()

    def accept(self, by_user):
        if by_user != self.to_user or self.denied or self.accepted:
            return False
        if self.to_user.make_friend_of(self.from_user):
            self.accepted = True
            self.save()
            return True
        else:
            raise Exception("A problem has occurred while trying to create a friendship edge.")

    def deny(self, by_user):
        if by_user != self.to_user or self.accepted or self.denied:
            return False
        self.denied = True
        self.save()
        return True


@receiver(models.signals.post_save, sender=FriendRequest, dispatch_uid='post_save_friend_request')
def post_save_friend_request(sender, instance, created, **kwargs):
    if created:
        friend_request_created.send(
            sender=FriendRequest,
            user=instance.from_user,
            instance=instance,
            receiver=instance.to_user
        )


class SocialGroupManagerMixin(object):

    def integrated_by(self, user):
        member_of = member_of_edge()
        count = graph.edge_count(user, member_of)
        ids = [node.pk for node, attributes, time in graph.edge_range(user, member_of, 0, count)]
        return self.get_queryset().filter(pk__in=ids)


class SocialGroupManager(SocialGroupManagerMixin, models.Manager):
    pass


class SocialGroupCurrentSiteManager(SocialGroupManagerMixin, CurrentSiteManager):
    pass


class SocialGroup(models.Model):
    creator = models.ForeignKey(User, related_name='created_groups', verbose_name=_(u'creator'))
    name = models.CharField(_(u'name'), max_length=255)
    slug = models.SlugField(_(u'slug'), max_length=255)
    description = models.TextField(_(u'description'))
    closed = models.BooleanField(_(u'closed'), default=False)
    administrators = models.ManyToManyField(
        User, related_name='managed_groups', verbose_name=_(u'administrators'), blank=True
    )
    created = models.DateTimeField(_(u'creation date'), auto_now_add=True)

    site = models.ForeignKey(Site, verbose_name=_(u'site'))

    def images_upload(self, filename):
        salt, hash_string = generate_sha1(self.pk)
        return 'site-%s/groups/%s/%s/%s' % (
            self.site.pk, self.creator.pk, hash_string,
            filename)

    image = models.ImageField(verbose_name=_(u'image'), upload_to=images_upload, null=True, blank=True, max_length=500)

    objects = SocialGroupManager()
    on_site = SocialGroupCurrentSiteManager()

    class Meta:
        unique_together = ('slug', 'site')
        verbose_name = _(u'social group')
        verbose_name_plural = _(u'social groups')

    def __init__(self, *args, **kwargs):
        super(SocialGroup, self).__init__(*args, **kwargs)
        if not self.pk and not self.site_id:
            self.site_id = Site.objects.get_current().pk

    @models.permalink
    def get_absolute_url(self):
        return 'group:details', [self.slug]

    @models.permalink
    def get_members_url(self):
        return 'group:members', [self.slug]

    @models.permalink
    def get_feed_url(self):
        return 'group:feed', [self.slug]

    @models.permalink
    def get_requests_url(self):
        return 'group:requests', [self.slug]

    @models.permalink
    def get_membership_buttons_url(self):
        return 'group:membership_buttons', [self.slug]

    @models.permalink
    def get_edit_url(self):
        return 'group:edit', [self.slug]

    @models.permalink
    def get_edit_inline_url(self):
        return 'group:edit_inline', [self.slug]

    @models.permalink
    def get_comment_url(self):
        return 'group:comment', [self.slug]

    @models.permalink
    def get_comment_inline_url(self):
        return 'group:comment_inline', [self.slug]

    @models.permalink
    def get_post_link_url(self):
        return 'group:post_link', [self.slug]

    @models.permalink
    def get_post_link_inline_url(self):
        return 'group:post_link_inline', [self.slug]

    @models.permalink
    def get_post_photo_url(self):
        return 'group:post_photo', [self.slug]

    @models.permalink
    def get_post_photo_inline_url(self):
        return 'group:post_photo_inline', [self.slug]

    @models.permalink
    def get_join_url(self):
        return 'group:join', [self.slug]

    @models.permalink
    def get_request_membership_url(self):
        return 'group:request_membership', [self.slug]

    @models.permalink
    def get_request_membership_inline_url(self):
        return 'group:request_membership_inline', [self.slug]

    @property
    def members(self):
        return graph.edge_count(self, integrated_by_edge())

    @property
    def member_list(self):
        edge = integrated_by_edge()
        count = graph.edge_count(self, edge)
        return [user for user, attributes, time in graph.edge_range(self, edge, 0, count)]

    def specific_role_member_list(self, role):
        edge = integrated_by_edge()
        count = graph.edge_count(self, edge)
        return [user for user, attributes, time in graph.edge_range(self, edge, 0, count) if attributes['role'] == role]

    @property
    def member_role_list(self):
        edge = integrated_by_edge()
        count = graph.edge_count(self, edge)
        return dict([(user.pk, attributes.get('role', 'member'))
                     for user, attributes, time in graph.edge_range(self, edge, 0, count)])

    def has_admin(self, user):
        return user == self.creator or user in self.administrators.all()

    def has_member(self, user):
        return graph.edge_get(user, member_of_edge(), self) is not None

    def relationship_with(self, user):
        edge = graph.edge_get(user, member_of_edge(), self)
        return user, edge.attributes.get('role', 'member') if edge else None

    def add_member(self, member, acceptor=None):
        if not acceptor:
            acceptor = member
        if self.closed and not self.has_admin(acceptor):
            return False
        _edge = graph.edge(member, self, member_of_edge(), self.site, {'role': 'member'})
        if _edge:
            social_group_member_added.send(
                sender=SocialGroup,
                group=self,
                member=member,
                user=acceptor
            )
            return True
        else:
            raise Exception("A problem has occurred while trying to create a membership edge.")

    def __unicode__(self):
        return u"%s" % self.name


@receiver(models.signals.pre_save, sender=SocialGroup, dispatch_uid='fill_social_group_slug')
def fill_social_group_slug(sender, instance, **kwargs):
    if not instance.pk and not instance.slug:
        instance.slug = slugify(instance.name)
        good_slug = False
        counter = 1
        while not good_slug:
            if instance.__class__.objects.filter(slug=instance.slug, site=instance.site).exists():
                instance.slug = instance.slug[:-1] + '%s' % counter
                counter += 1
            else:
                good_slug = True


@receiver(models.signals.post_save, sender=SocialGroup, dispatch_uid='post_save_social_group')
def post_save_social_group(sender, instance, created, **kwargs):
    if created:
        # add creator to members
        graph.edge(instance.creator, instance, member_of_edge(), instance.site, {'role': 'creator'})
        social_group_created.send(sender=SocialGroup, instance=instance, user=instance.creator)


@receiver(models.signals.m2m_changed, sender=SocialGroup.administrators.through, dispatch_uid='post_m2m_changed_social_group')
def post_m2m_changed_social_group(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    member_of = member_of_edge()
    if not reverse:  # the call has modified the direct relationship SocialGroup.administrators
        group = instance
        if action == 'post_clear':
            for admin in group.specific_role_member_list('admin'):
                graph.no_edge(admin, group, member_of, group.site)
        else:
            admins = model.objects.filter(pk__in=list(pk_set))
            if action == 'post_add':
                for admin in admins:
                    graph.edge(admin, group, member_of, group.site, {'role': 'admin'})
            elif action == 'post_remove':
                for admin in admins:
                    graph.no_edge(admin, group, member_of, group.site)
    else:  # the call has modified the reverse relationship: User.groups_administrated_by
        admin = instance
        if action == 'post_clear':
            for group in admin.specific_role_social_group_list('admin'):
                graph.no_edge(admin, group, member_of, group.site)
        else:
            groups = model.objects.filter(pk__in=list(pk_set))
            if action == 'post_add':
                for group in groups:
                    graph.edge(admin, group, member_of, group.site, {'role': 'admin'})
            elif action == 'post_remove':
                for group in groups:
                    graph.no_edge(admin, group, member_of, group.site)


class GroupMembershipRequest(models.Model):
    requester = models.ForeignKey(User, related_name='requested_group_memberships', verbose_name=_(u'requester'))
    group = models.ForeignKey(SocialGroup, related_name='aspirants', verbose_name=_(u'group'))
    message = models.TextField(blank=True, verbose_name=_(u'message'))
    accepted = models.BooleanField(default=False, verbose_name=_(u'accepted'), blank=True)
    denied = models.BooleanField(default=False, verbose_name=_(u'denied'), blank=True)
    acceptor = models.ForeignKey(
        User, related_name='accepted_group_memberships', verbose_name=_(u'decider'), null=True, blank=True
    )

    class Meta:
        verbose_name = _(u'group membership request')
        verbose_name_plural = _(u'group membership requests')

    @models.permalink
    def get_accept_url(self):
        return 'group:accept_request', [], {'slug': self.group.slug, 'pk': self.pk}

    @models.permalink
    def get_deny_url(self):
        return 'group:deny_request', [], {'slug': self.group.slug, 'pk': self.pk}

    def accept(self, by_user):
        if not self.group.has_admin(by_user) or self.denied or self.accepted:
            return False
        if self.group.add_member(self.requester, by_user):
            self.accepted = True
            self.acceptor = by_user
            self.save()
            return True
        else:
            return False

    def deny(self, by_user):
        if not self.group.has_admin(by_user) or self.accepted or self.denied:
            return False
        self.denied = True
        self.acceptor = by_user
        self.save()
        return True


@receiver(models.signals.post_save, sender=GroupMembershipRequest, dispatch_uid='post_save_group_membership_request')
def post_save_group_membership_request(sender, instance, created, **kwargs):
    if created:
        social_group_membership_request_created.send(
            sender=GroupMembershipRequest,
            instance=instance,
            user=instance.requester,
            group=instance.group
        )


class GroupPost(models.Model):
    creator = models.ForeignKey(User, related_name='posts', verbose_name=_(u'creator'))
    group = models.ForeignKey(SocialGroup, related_name='posts', verbose_name=_(u'group'))
    comment = models.TextField(_(u'comment'))
    url = models.URLField(_(u'url'), blank=True)

    def images_upload(self, filename):
        group_salt, group_hash_string = generate_sha1(self.group.pk)
        salt, hash_string = generate_sha1(self.pk)
        return 'site-%s/groups/%s/%s/%s/%s/%s' % (
            self.group.site.pk, self.group.creator.pk, group_hash_string, self.creator.pk, hash_string,
            filename)

    image = models.ImageField(_(u'cover image'), upload_to=images_upload, null=True, blank=True, max_length=500)

    class Meta(object):
        verbose_name = _(u'group post')
        verbose_name_plural = _(u'group posts')


@receiver(models.signals.post_save, sender=GroupPost, dispatch_uid='post_save_group_post')
def post_save_group_post(sender, instance, created, **kwargs):
    if created:
        social_group_post_created.send(sender=GroupPost, user=instance.creator, instance=instance)


@receiver(social_group_post_created, sender=GroupPost, dispatch_uid='social_network_group_post')
def social_network_group_post(instance, user, **kwargs):
    from notifications import create_event
    create_event(user, group_post_event_type(), instance, _(u'A new post has been added to a group'))


class GroupFeedItem(models.Model):
    group = models.ForeignKey(SocialGroup, related_name='feed_items')
    event = models.ForeignKey(Event, related_name='feed_items')
    template_config = models.ForeignKey(NotificationTemplateConfig)

    site = models.ForeignKey(Site)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    class Meta(object):
        verbose_name = _(u'group feed item')
        verbose_name_plural = _(u'group feed item')
        ordering = ('-event__date',)

    def __init__(self, *args, **kwargs):
        super(GroupFeedItem, self).__init__(*args, **kwargs)
        if not self.pk and not self.site_id:
            self.site_id = self.event.site_id or Site.objects.get_current().pk


class FeedComment(models.Model):
    creator = models.ForeignKey(User, related_name='feed_comments', verbose_name=_(u'creator'))
    receiver = models.ForeignKey(User, related_name='feed_received_comments', verbose_name=_(u'receiver'))
    comment = models.TextField(_(u'comment'))

    class Meta(object):
        verbose_name = _(u'profile comment')
        verbose_name_plural = _(u'profile comments')


@receiver(models.signals.post_save, sender=FeedComment, dispatch_uid='post_save_feed_comment')
def post_save_feed_comment(sender, instance, created, **kwargs):
    if created:
        profile_comment_created.send(sender=FeedComment, user=instance.creator, instance=instance)
