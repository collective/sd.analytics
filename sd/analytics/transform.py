from BeautifulSoup import BeautifulSoup
from Products.CMFPlone.interfaces import IPloneSiteRoot
from collective.dancing import utils
from interfaces import IAnalytics
from zope import component
from zope import interface
from zope.component.hooks import getSite

import collective.singing.interfaces
import re
import urllib

relative_exp = re.compile('^(?!(\w+://|mailto:|javascript:|/))')


class Analytics(object):
    interface.implements(collective.singing.interfaces.ITransform)

    def __init__(self, context):
        self.context = context

    @property
    def site(self):
        """ Get the plone site. Bit hackish, to make it work with the
        simple test setup in transform.txt while still being properly
        wrapped """
        site = getSite()
        if not site:
            site = component.getUtility(IPloneSiteRoot)
            site = utils.fix_request(site, 0)
        return site

    @property
    def settings(self):
        return IAnalytics(self.site.portal_newsletters)

    @property
    def params(self):
        return dict([(k, v) for k, v in self.settings.items()
                     if v and k != 'enabled'])

    @property
    def active(self):
        return self.settings['enabled']

    def __call__(self, text, subscription):
        if not self.active:
            return text

        soup = BeautifulSoup(text, fromEncoding='UTF-8')

        for attr in ('href', 'src'):
            for tag in soup.findAll(attrs={attr: lambda x: x}):
                url, query = urllib.splitquery(tag[attr])

                if (not url.startswith(self.site.absolute_url()) and
                        not relative_exp.match(url)):
                    continue

                params = self.params
                if 'utm_campaign' not in params:
                    params.update(dict(utm_campaign=subscription.channel.name))
                if query is not None:
                    params.update(dict(['=' in q and q.split('=') or (q, '')
                                  for q in query.split('&') if q]))

                tag[attr] = u'%s?%s' % (url, urllib.urlencode(params))

        return str(soup)
