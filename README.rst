
=====================
Django Social Network
=====================

Django social network for Django>=1.6.1

Allows to create a basic social network including friendship and social group dynamics

Changelog
=========

0.4.1
-----

- Added GroupFeedItem field "erased" to mark has erased all deleted instance.

0.4.0
-----

- Added functionality to edit/delete GroupPost
- Added functionality to Share to social networks and Social Groups as django-content-interactions
- middleware removed
- Changed User proxy to abstraction

0.3.0
-----

- Model Refactoring.
- Social Middleware.


0.2.7
-----

- Fixed error in group request accepting/denying authorization logic.

0.2.6
-----

- Fix toggle interaction success implementation.

0.2.5
-----

- Fixed error in group transport settings.


0.2.4
-----

- Adding functionality for editing social groups.


0.2.3
-----

- Fixed some errors.

0.2.2
-----

- Migration support for link sharing in social groups.

0.2.1
-----

- Link sharing in social groups.

0.2.0
-----

- General refactoring to get more instinctive usage.

0.1.1
-----

- Adding functionality to django user model, changed urls and views accordingly.
- js functionality for toggle relationships

0.1.0
-----

-First Commit

Notes
-----

PENDING...

Usage
-----

1. Run ``python setup.py install`` to install.

2. Modify your Django settings to use ``social_network``:


