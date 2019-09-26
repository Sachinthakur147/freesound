# -*- coding: utf-8 -*-
#
# Freesound is (c) MUSIC TECHNOLOGY GROUP, UNIVERSITAT POMPEU FABRA
#
# Freesound is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Freesound is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     See AUTHORS file.
#
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.conf import settings
from utils.search.search_general import search_prepare_parameters, split_filter_query, search_prepare_query
from search.forms import SEARCH_DEFAULT_SORT, SEARCH_SORT_OPTIONS_WEB


class SearchUtilsTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_search_prepare_parameters_without_query_params(self):
        request = self.factory.get(reverse('sounds-search'))
        query_params, advanced_search_params_dict, extra_vars = search_prepare_parameters(request)

        expected_default_query_params = {
            'id_weight': settings.DEFAULT_SEARCH_WEIGHTS['id'],
            'tag_weight': settings.DEFAULT_SEARCH_WEIGHTS['tag'],
            'description_weight': settings.DEFAULT_SEARCH_WEIGHTS['description'],
            'username_weight': settings.DEFAULT_SEARCH_WEIGHTS['username'],
            'pack_tokenized_weight': settings.DEFAULT_SEARCH_WEIGHTS['pack_tokenized'],
            'original_filename_weight': settings.DEFAULT_SEARCH_WEIGHTS['original_filename'],
            'sort': [SEARCH_DEFAULT_SORT],
            'sounds_per_page': settings.SOUNDS_PER_PAGE,
            'current_page': 1,
            'grouping': u'1',
            'filter_query': u'',
            'search_query': u'',
        }

        expected_extra_vars = {
            'advanced': '',
            'sort_unformatted': None,
            'filter_query_link_more_when_grouping_packs': '',
            'sort_options': SEARCH_SORT_OPTIONS_WEB
        }

        self.assertDictEqual(query_params, expected_default_query_params)
        self.assertDictEqual(advanced_search_params_dict, {})
        self.assertDictEqual(extra_vars, expected_extra_vars)

    def test_search_prepare_parameters_with_query_params(self):
        # "dog" query, search only in tags and descriptions, duration from 1-10 sec, only geotag, sort by duration, no group by pack
        url_query_str = '?q=dog&f=duration:[1+TO+10]+is_geotagged:1&s=duration+desc&advanced=1&a_tag=1&a_description=1&g='
        request = self.factory.get(reverse('sounds-search')+url_query_str)
        query_params, advanced_search_params_dict, extra_vars = search_prepare_parameters(request)

        expected_default_query_params = {
            'id_weight': 0,
            'tag_weight': settings.DEFAULT_SEARCH_WEIGHTS['tag'],
            'description_weight': settings.DEFAULT_SEARCH_WEIGHTS['description'],
            'username_weight': 0,
            'pack_tokenized_weight': 0,
            'original_filename_weight': 0,
            'sort': [u'duration desc'],
            'sounds_per_page': settings.SOUNDS_PER_PAGE,
            'current_page': 1,
            'grouping': u'',
            'filter_query': u'duration:[1 TO 10] is_geotagged:1',
            'search_query': u'dog',
        }

        expected_extra_vars = {
            'advanced': u'1',
            'sort_unformatted': u'duration desc',
            'filter_query_link_more_when_grouping_packs': u'duration:[1+TO+10]+is_geotagged:1',
            'sort_options': SEARCH_SORT_OPTIONS_WEB
        }

        expected_advanced_search_params_dict = {
            'a_tag': u'1', 
            'a_username': '', 
            'a_description': u'1', 
            'a_packname': '', 
            'a_filename': '', 
            'a_soundid': '',
        }

        self.assertDictEqual(query_params, expected_default_query_params)
        self.assertDictEqual(advanced_search_params_dict, expected_advanced_search_params_dict)
        self.assertDictEqual(extra_vars, expected_extra_vars)

    def test_search_prepare_parameters_non_ascii_query(self):
        # Simple test to check if some non ascii characters are correctly handled by search_prepare_parameters()
        request = self.factory.get(reverse('sounds-search')+u'?q=Æ æ ¿ É')
        query_params, advanced_search_params_dict, extra_vars = search_prepare_parameters(request)
        self.assertEqual(query_params['search_query'], u'\xc6 \xe6 \xbf \xc9')

    def test_split_filter_query_duration_and_facet(self):
        # We check that the combination of a duration filter and a facet filter (CC Attribution) works correctly.
        filter_query_string = u'duration:[0 TO 10] license:"Attribution"'
        filter_query_split = split_filter_query(filter_query_string, '')

        # duraton filter is not a facet, but should stay present when removing a facet.
        expected_filter_query_split = [
            {'remove_url': u'duration:[0 TO 10]', 'name': u'license:Attribution'}, 
        ]

        # we use assertIn because the unicode strings that split_filter_query generates can incorporate 
        # additional spaces, which is not a problem.
        self.assertIn(expected_filter_query_split[0]['name'], filter_query_split[0]['name'])
        self.assertIn(expected_filter_query_split[0]['remove_url'], filter_query_split[0]['remove_url'])

    def test_split_filter_query_cluster_facet(self):
        # We check that the combination of a duration filter, a facet filter (CC Attribution) and a cluster filter
        # works correctly.
        filter_query_string = u'duration:[0 TO 10] license:"Attribution"'
        filter_query_split = split_filter_query(filter_query_string, '1')

        expected_filter_query_split = [
            {'remove_url': u'duration:[0 TO 10]', 'name': u'license:Attribution'}, 
            {'remove_url': u'duration:[0 TO 10] license:"Attribution"', 'name': 'Cluster #1'}
        ]

        # check that the cluster facet exists
        filter_query_names = [filter_query_dict['name'] for filter_query_dict in expected_filter_query_split]
        self.assertIn('Cluster #1', filter_query_names)

        # the order does not matter for the list of facet dicts.
        # we get the index of the correspondings facets dicts.
        cc_attribution_facet_dict_idx = filter_query_names.index('license:Attribution')
        cluster_facet_dict_idx = filter_query_names.index('Cluster #1')

        self.assertIn(expected_filter_query_split[0]['name'], 
                      filter_query_split[cc_attribution_facet_dict_idx]['name'])
        self.assertIn(expected_filter_query_split[0]['remove_url'], 
                      filter_query_split[cc_attribution_facet_dict_idx]['remove_url'])

        self.assertIn(expected_filter_query_split[1]['name'], 
                      filter_query_split[cluster_facet_dict_idx]['name'])
        self.assertIn(expected_filter_query_split[1]['remove_url'], 
                      filter_query_split[cluster_facet_dict_idx]['remove_url'])

    def test_search_prepare_query(self):
        # we test that some query parameters get correctly setted in the Solr query object.
        query_params = {
            'search_query': u'cat',
            'filter_query': u'duration:[1 TO 10] is_geotagged:1',
            'sort': [u'duration desc'],
            'current_page': 1,
            'sounds_per_page': settings.SOUNDS_PER_PAGE,
            'id_weight': 10,
            'tag_weight': 0,
            'description_weight': 0,
            'username_weight': 0,
            'pack_tokenized_weight': 0,
            'original_filename_weight': 0,
            'grouping': True,
            'in_ids': [],
        }

        query = search_prepare_query(**query_params)

        self.assertEqual(query.params['q'], 'cat')
        self.assertEqual(query.params['qf'], 'id^10')
        self.assertEqual(query.params['fq'], 'duration:[1 TO 10] is_geotagged:1')
        self.assertTrue(query.params['group'])
        
    def test_search_prepare_query_cluster_filter(self):
        # we test that a cluster filter removes all other filters and correctly adds filters by id.
        query_params = {
            'search_query': u'cat',
            'filter_query': u'duration:[1 TO 10] is_geotagged:1',
            'sort': [u'duration desc'],
            'current_page': 1,
            'sounds_per_page': settings.SOUNDS_PER_PAGE,
            'in_ids': ["1", "2", "3"],
        }

        query = search_prepare_query(**query_params)
        self.assertEqual(query.params['fq'], "id:1 OR id:2 OR id:3")
        