# -*- coding: utf-8 -*-
import logging
from ..utils.crawler import Crawler

logger = logging.getLogger(__name__)
search_url = 'https://bestlightnovel.com/getsearchstory'
novel_page_url = 'https://bestlightnovel.com/novel_%s'
change_bad_words_off = 'https://bestlightnovel.com/change_bad_words_off'


class BestLightNovel(Crawler):
    base_url = 'https://bestlightnovel.com/'

    def search_novel(self, query):
        data = self.submit_form(search_url, {
            'searchword': query
        }).json()

        results = []
        for novel in data:
            titleSoup = self.make_soup(novel['name'])
            results.append({
                'title': titleSoup.body.text.title(),
                'url': novel_page_url % novel['id_encode'],
                'info': 'Latest: %s' % novel['lastchapter'],
            })
        # end for
        return results
    # end def

    def read_novel_info(self):
        '''Get novel title, autor, cover etc'''
        logger.debug('Visiting %s', self.novel_url)
        soup = self.get_soup(self.novel_url)

        # self.novel_title = soup.select_one('h1.entry-title').text.strip()
        self.novel_title = soup.select_one('div.entry-header h1').text.strip()
        logger.info('Novel title: %s', self.novel_title)

        try:
            novel_data = self.submit_form(search_url, {
                'searchword': self.novel_title
            }).json()
            self.novel_cover = novel_data[0]['image']
            self.novel_author = novel_data[0]['author']
        except Exception:
            logger.debug('Failed getting novel info.\n%s', Exception)
        # end try

        for a in reversed(soup.select('#list_chapter .chapter-list a')):
            chap_id = len(self.chapters) + 1
            vol_id = len(self.chapters) // 100 + 1
            if len(self.chapters) % 100 == 0:
                self.volumes.append({'id': vol_id})
            # end if
            self.chapters.append({
                'id': chap_id,
                'volume': vol_id,
                'title': a.text.strip(),
                'url': self.absolute_url(a['href']),
            })
        # end for

        self.get_response(change_bad_words_off)
    # end def

    def download_chapter_body(self, chapter):
        '''Download body of a single chapter and return as clean html format.'''
        logger.info('Downloading %s', chapter['url'])
        soup = self.get_soup(chapter['url'])

        logger.debug(soup.title.string)

        if 'Chapter' in soup.select_one('h1').text:
            chapter['title'] = soup.select_one('h1').text
        else:
            chapter['title'] = chapter['title']
        # end if

        self.blacklist_patterns = [
            r'^translat(ed by|or)',
            r'(volume|chapter) .?\d+',
        ]

        contents = soup.select_one('#vung_doc')
        body = self.extract_contents(contents)
        return '<p>' + '</p><p>'.join(body) + '</p>'
    # end def
# end class
