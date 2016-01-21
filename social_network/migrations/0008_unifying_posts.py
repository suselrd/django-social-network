# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

POST_ACTION_READ_AS = getattr(settings, 'SOCIAL_NETWORK_POST_ACTION_READ_AS', 'Post')
POST_EVENT_READ_AS = getattr(settings, 'SOCIAL_NETWORK_POST_EVENT_READ_AS', 'Community Post')


class Migration(DataMigration):

    def forwards(self, orm):
        
        post_event_type = 'social_group_post'
        comment_event_type = 'social_group_comment'
        shared_link_event_type = 'social_group_shared_link'
        photo_event_type = 'social_group_photo'

        category, created = orm['notifications.EventTypeCategory'].objects.get_or_create(
            name='social_network_category',
            defaults={'read_as': 'Social'}
        )
        post, created = orm['notifications.Action'].objects.get_or_create(
            name='post',
            defaults={'read_as': POST_ACTION_READ_AS}
        )
        post_event_type, created = orm['notifications.EventType'].objects.get_or_create(
            name=post_event_type,
            action=post,
            target_type='social_network.socialgroup',
            defaults={
                'read_as': POST_EVENT_READ_AS,
                'category': category,
                'immediate': True
            }
        )

        try:
            group_transport = orm['notifications.Transport'].objects.get(
                name='group_transport',
                cls='social_network.transports.GroupFeedTransport',
            )
            post_template_config, created = orm['notifications.NotificationTemplateConfig'].objects.get_or_create(
                event_type=post_event_type,
                transport=group_transport,
                defaults={
                    'template_path': 'social_network/group/detail/post.html'
                }
            )

            try:
                comment_event_type = orm['notifications.EventType'].objects.get(name=comment_event_type)
                for event in comment_event_type.event_set.all():
                    comment = event.target_object
                    post = orm.GroupPost.objects.create(
                        creator=comment.creator,
                        group=comment.group,
                        comment=comment.comment
                    )
                    event.type = post_event_type
                    event.target_object = post
                    event.save()
                orm.GroupFeedItem.objects.filter(
                    template_config__event_type=comment_event_type,
                    template_config__transport=group_transport
                ).update(template_config=post_template_config)
            except ObjectDoesNotExist:
                pass

            try:
                shared_link_event_type = orm['notifications.EventType'].objects.get(name=shared_link_event_type)
                for event in shared_link_event_type.event_set.all():
                    shared_link = event.target_object
                    post = orm.GroupPost.objects.create(
                        creator=shared_link.creator,
                        group=shared_link.group,
                        comment=shared_link.comment,
                        url=shared_link.url
                    )
                    event.type = post_event_type
                    event.target_object = post
                    event.save()
                orm.GroupFeedItem.objects.filter(
                    template_config__event_type=shared_link_event_type,
                    template_config__transport=group_transport
                ).update(template_config=post_template_config)
            except ObjectDoesNotExist:
                pass

            try:
                photo_event_type = orm['notifications.EventType'].objects.get(name=photo_event_type)
                for event in photo_event_type.event_set.all():
                    image = event.target_object
                    post = orm.GroupPost.objects.create(
                        creator=image.creator,
                        group=image.group,
                        comment=image.comment,
                        image=image.image
                    )
                    event.type = post_event_type
                    event.target_object = post
                    event.save()
                orm.GroupFeedItem.objects.filter(
                    template_config__event_type=photo_event_type,
                    template_config__transport=group_transport
                ).update(template_config=post_template_config)
            except ObjectDoesNotExist:
                pass
        except ObjectDoesNotExist:
            pass

    def backwards(self, orm):

        post_event_type = 'social_group_post'
        comment_event_type = 'social_group_comment'
        shared_link_event_type = 'social_group_shared_link'
        photo_event_type = 'social_group_photo'

        comment_event_type, created = orm['notifications.EventType'].objects.get_or_create(
            name=comment_event_type
        )
        shared_link_event_type, created = orm['notifications.EventType'].objects.get_or_create(
            name=shared_link_event_type
        )
        photo_event_type, created = orm['notifications.EventType'].objects.get_or_create(
            name=photo_event_type
        )

        try:
            post_event_type = orm['notifications.EventType'].objects.get(name=post_event_type)
            for event in post_event_type.event_set.all():
                post = event.target_object
                if post.url:
                    shared_link = orm.GroupSharedLink.objects.create(
                        creator=post.creator,
                        group=post.group,
                        comment=post.comment,
                        url=post.url
                    )
                    event.type = shared_link_event_type
                    event.target_object = shared_link
                elif post.image:
                    image = orm.GroupImage.objects.create(
                        creator=post.creator,
                        group=post.group,
                        comment=post.comment,
                        image=post.image
                    )
                    event.type = photo_event_type
                    event.target_object = image
                else:
                    comment = orm.GroupComment.objects.create(
                        creator=post.creator,
                        group=post.group,
                        comment=post.comment
                    )
                    event.type = comment_event_type
                    event.target_object = comment
                event.save()
        except ObjectDoesNotExist:
            pass

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'notifications.action': {
            'Meta': {'object_name': 'Action'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'read_as': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'notifications.event': {
            'Meta': {'object_name': 'Event'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'extra_data': ('notifications.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']", 'null': 'True'}),
            'target_pk': ('django.db.models.fields.TextField', [], {}),
            'target_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'event'", 'to': u"orm['contenttypes.ContentType']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notifications.EventType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': u"orm['auth.User']"})
        },
        'notifications.eventattendantsconfig': {
            'Meta': {'unique_together': "(('event_type', 'transport'),)", 'object_name': 'EventAttendantsConfig'},
            'event_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attendants_configurations'", 'to': "orm['notifications.EventType']"}),
            'get_attendants_methods': ('notifications.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'transport': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attendants_configurations'", 'to': "orm['notifications.Transport']"})
        },
        'notifications.eventtype': {
            'Meta': {'object_name': 'EventType'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notifications.Action']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notifications.EventTypeCategory']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immediate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'read_as': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'target_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'transports': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'event_types'", 'symmetrical': 'False', 'through': "orm['notifications.EventAttendantsConfig']", 'to': "orm['notifications.Transport']"})
        },
        'notifications.eventtypecategory': {
            'Meta': {'object_name': 'EventTypeCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'read_as': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'notifications.notificationtemplateconfig': {
            'Meta': {'unique_together': "(('event_type', 'transport', 'context'),)", 'object_name': 'NotificationTemplateConfig'},
            'context': ('django.db.models.fields.CharField', [], {'default': "u'default'", 'max_length': '255'}),
            'data': ('notifications.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'event_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notifications.EventType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'single_template_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'template_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'transport': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notifications.Transport']"})
        },
        'notifications.transport': {
            'Meta': {'object_name': 'Transport'},
            'allows_context': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allows_freq_config': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allows_subscription': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cls': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'delete_sent': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'social_network.feedcomment': {
            'Meta': {'object_name': 'FeedComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'feed_comments'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'receiver': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'feed_received_comments'", 'to': u"orm['auth.User']"})
        },
        u'social_network.friendrequest': {
            'Meta': {'object_name': 'FriendRequest'},
            'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'denied': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_outgoing_friend_requests'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_incoming_friend_requests'", 'to': u"orm['auth.User']"})
        },
        u'social_network.groupcomment': {
            'Meta': {'object_name': 'GroupComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_groupcomment_set_post'", 'to': u"orm['auth.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_groupcomment_set_post'", 'to': u"orm['social_network.SocialGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'social_network.groupfeeditem': {
            'Meta': {'object_name': 'GroupFeedItem'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notifications.Event']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social_network.SocialGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'template_config': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notifications.NotificationTemplateConfig']"})
        },
        u'social_network.groupimage': {
            'Meta': {'object_name': 'GroupImage'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_groupimage_set_post'", 'to': u"orm['auth.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_groupimage_set_post'", 'to': u"orm['social_network.SocialGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        u'social_network.groupmembershiprequest': {
            'Meta': {'object_name': 'GroupMembershipRequest'},
            'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'acceptor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'accepted_group_memberships'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'denied': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'aspirants'", 'to': u"orm['social_network.SocialGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'requester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requested_group_memberships'", 'to': u"orm['auth.User']"})
        },
        u'social_network.grouppost': {
            'Meta': {'object_name': 'GroupPost'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_grouppost_set_post'", 'to': u"orm['auth.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_grouppost_set_post'", 'to': u"orm['social_network.SocialGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        u'social_network.groupsharedlink': {
            'Meta': {'object_name': 'GroupSharedLink'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_groupsharedlink_set_post'", 'to': u"orm['auth.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'(app_label)s_groupsharedlink_set_post'", 'to': u"orm['social_network.SocialGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'social_network.socialgroup': {
            'Meta': {'object_name': 'SocialGroup'},
            'administrators': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'groups_administrated_by'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups_created_by'", 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"})
        }
    }

    complete_apps = ['social_network']
    symmetrical = True
