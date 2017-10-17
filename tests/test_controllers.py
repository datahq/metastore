import time
import unittest
from importlib import import_module
from elasticsearch import Elasticsearch, NotFoundError

LOCAL_ELASTICSEARCH = 'localhost:9200'

module = import_module('metastore.controllers')

class SearchTest(unittest.TestCase):

    # Actions
    MAPPING = {
        'datahub': {
            'type': 'object',
            'properties': {
                'owner': {
                    "type": "string",
                    "index": "not_analyzed",
                }
            }
        }
    }

    def setUp(self):

        # Clean index
        self.es = Elasticsearch(hosts=[LOCAL_ELASTICSEARCH])
        try:
            self.es.indices.delete(index='datahub')
        except NotFoundError:
            pass
        self.es.indices.create('datahub')
        mapping = {'dataset': {'properties': self.MAPPING}}
        self.es.indices.put_mapping(doc_type='dataset',
                                    index='datahub',
                                    body=mapping)

    def search(self, kind, *args, **kwargs):
        ret = module.search(kind, *args, **kwargs)
        self.assertLessEqual(len(ret['results']), ret['summary']['total'])
        return ret['results'], ret['summary']

    def indexSomeRecords(self, amount):
        self.es.indices.delete(index='datahub')
        for i in range(amount):
            body = {
                'name': True,
                'title': i,
                'license': 'str%s' % i,
                'datahub': {
                    'name': 'innername',
                    'findability': 'published',
                    'stats': {
                        'bytes': 10
                    }
                }
            }
            self.es.index('datahub', 'dataset', body)
        self.es.indices.flush('datahub')

    def indexSomeRecordsToTestMapping(self):
        for i in range(3):
            body = {
                'name': 'package-id-%d' % i,
                'title': 'This dataset is number test%d' % i,
                'datahub': {
                    'owner': 'BlaBla%d@test2.com' % i,
                    'findability': 'published',
                    'stats': {
                        'bytes': 10
                    }
                },
            }
            self.es.index('datahub', 'dataset', body)
        self.es.indices.flush('datahub')

    def indexSomeRealLookingRecords(self, amount):
        for i in range(amount):
            body = {
                'name': 'package-id-%d' % i,
                'title': 'This dataset is number%d' % i,
                'datahub': {
                    'owner': 'The one and only owner number%d' % (i+1),
                    'findability': 'published',
                    'stats': {
                        'bytes': 10
                    }
                },
                'loaded': True
            }
            self.es.index('datahub', 'dataset', body)
        self.es.indices.flush('datahub')

    def indexSomePrivateRecords(self):
        i = 0
        for owner in ['owner1', 'owner2']:
            for private in ['published', 'else']:
                for content in ['cat', 'dog']:
                    body = {
                        'name': '%s-%s-%s' % (owner, private, content),
                        'title': 'This dataset is number%d, content is %s' % (i, content),
                        'datahub': {
                            'owner': 'The one and only owner number%d' % (i+1),
                            'ownerid': owner,
                            'findability': private,
                            'stats': {
                                'bytes': 10
                            }
                        }
                    }
                    i += 1
                    self.es.index('datahub', 'dataset', body)
        self.es.indices.flush('datahub')

    # Tests
    def test___search___all_values_and_empty(self):
        self.assertEquals(self.search('dataset', None), ([], {'total': 0, 'totalBytes': 0.0}))

    def test___search___all_values_and_one_result(self):
        self.indexSomeRecords(1)
        res, summary = self.search('dataset', None)
        self.assertEquals(len(res), 1)
        self.assertEquals(summary['total'], 1)
        self.assertEquals(summary['totalBytes'], 10)

    def test___search___all_values_and_two_results(self):
        self.indexSomeRecords(2)
        res, summary = self.search('dataset', None)
        self.assertEquals(len(res), 2)
        self.assertEquals(summary['total'], 2)
        self.assertEquals(summary['totalBytes'], 20)

    def test___search___filter_simple_property(self):
        self.indexSomeRecords(10)
        res, summary = self.search('dataset', None, {'license': ['"str7"']})
        self.assertEquals(len(res), 1)
        self.assertEquals(summary['total'], 1)
        self.assertEquals(summary['totalBytes'], 10)

    def test___search___filter_numeric_property(self):
        self.indexSomeRecords(10)
        res, summary = self.search('dataset', None, {'title': ["7"]})
        self.assertEquals(len(res), 1)
        self.assertEquals(summary['total'], 1)
        self.assertEquals(summary['totalBytes'], 10)

    def test___search___filter_boolean_property(self):
        self.indexSomeRecords(10)
        res, summary = self.search('dataset', None, {'name': ["true"]})
        self.assertEquals(len(res), 10)
        self.assertEquals(summary['total'], 10)
        self.assertEquals(summary['totalBytes'], 100)

    def test___search___filter_multiple_properties(self):
        self.indexSomeRecords(10)
        res, summary = self.search('dataset', None, {'license': ['"str6"'], 'title': ["6"]})
        self.assertEquals(len(res), 1)
        self.assertEquals(summary['total'], 1)
        self.assertEquals(summary['totalBytes'], 10)

    def test___search___filter_multiple_values_for_property(self):
        self.indexSomeRecords(10)
        res, summary = self.search('dataset', None, {'license': ['"str6"','"str7"']})
        self.assertEquals(len(res), 2)
        self.assertEquals(summary['total'], 2)
        self.assertEquals(summary['totalBytes'], 20)

    def test___search___filter_inner_property(self):
        self.indexSomeRecords(7)
        res, summary = self.search('dataset', None, {"datahub.name": ['"innername"']})
        self.assertEquals(len(res), 7)
        self.assertEquals(summary['total'], 7)
        self.assertEquals(summary['totalBytes'], 70)

    def test___search___filter_no_results(self):
        res, summary = self.search('dataset', None, {'license': ['"str6"'], 'title': ["7"]})
        self.assertEquals(len(res), 0)
        self.assertEquals(summary['total'], 0)
        self.assertEquals(summary['totalBytes'], 0)

    def test___search___filter_bad_value(self):
        ret = module.search('dataset', None, {'license': ['str6'], 'title': ["6"]})
        self.assertEquals(ret['results'], [])
        self.assertEquals(ret['summary']['total'], 0)
        self.assertEquals(ret['summary']['totalBytes'], 0)
        self.assertIsNotNone(ret['error'])

    def test___search___filter_nonexistent_property(self):
        ret = module.search('dataset', None, {'license': ['str6'], 'boxing': ["6"]})
        self.assertEquals(ret['results'], [])
        self.assertEquals(ret['summary']['total'], 0)
        self.assertEquals(ret['summary']['totalBytes'], 0)
        self.assertIsNotNone(ret['error'])

    def test___search___returns_limited_size(self):
        self.indexSomeRecords(10)
        res, summary = self.search('dataset', None, {'size':['4']})
        self.assertEquals(len(res), 4)
        self.assertEquals(summary['total'], 10)
        self.assertEquals(summary['totalBytes'], 100)

    def test___search___not_allows_more_than_50(self):
        self.indexSomeRecords(105)
        res, summary = self.search('dataset', None, {'size':['105']})
        self.assertEquals(len(res), 100)
        self.assertEquals(summary['total'], 105)
        self.assertEquals(summary['totalBytes'], 1050)

    def test___search___returns_results_from_given_index(self):
        self.indexSomeRecords(5)
        res, summary = self.search('dataset', None, {'from':['3']})
        self.assertEquals(len(res), 2)
        self.assertEquals(summary['total'], 5)
        self.assertEquals(summary['totalBytes'], 50)

    def test___search___q_param_no_recs_no_results(self):
        self.indexSomeRealLookingRecords(0)
        res, summary = self.search('dataset', None, {'q': ['"owner"']})
        self.assertEquals(len(res), 0)
        self.assertEquals(summary['total'], 0)
        self.assertEquals(summary['totalBytes'], 0)

    def test___search___q_param_some_recs_no_results(self):
        self.indexSomeRealLookingRecords(2)
        res, summary = self.search('dataset', None, {'q': ['"writer"']})
        self.assertEquals(len(res), 0)
        self.assertEquals(summary['total'], 0)
        self.assertEquals(summary['totalBytes'], 0)

    def test___search___q_param_some_recs_some_results(self):
        self.indexSomeRealLookingRecords(2)
        res, summary = self.search('dataset', None, {'q': ['"number1"']})
        self.assertEquals(len(res), 1)
        self.assertEquals(summary['total'], 1)
        self.assertEquals(summary['totalBytes'], 10)

    def test___search___q_param_some_recs_all_results(self):
        self.indexSomeRealLookingRecords(10)
        res, summary = self.search('dataset', None, {'q': ['"dataset shataset"']})
        self.assertEquals(len(res), 10)
        self.assertEquals(summary['total'], 10)
        self.assertEquals(summary['totalBytes'], 100)

    def test___search___empty_anonymous_search(self):
        self.indexSomePrivateRecords()
        recs, _ = self.search('dataset', None)
        self.assertEquals(len(recs), 4)
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'owner1-published-cat',
                                  'owner2-published-cat',
                                  'owner1-published-dog',
                                  'owner2-published-dog',
                                  })

    def test___search___empty_authenticated_search(self):
        self.indexSomePrivateRecords()
        recs, _ = self.search('dataset', 'owner1')
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'owner1-published-cat',
                                  'owner1-else-cat',
                                  'owner2-published-cat',
                                  'owner1-published-dog',
                                  'owner1-else-dog',
                                  'owner2-published-dog',
                                  })
        self.assertEquals(len(recs), 6)

    def test___search___q_param_anonymous_search(self):
        self.indexSomePrivateRecords()
        recs, _ = self.search('dataset', None, {'q': ['"cat"']})
        self.assertEquals(len(recs), 2)
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'owner1-published-cat',
                                  'owner2-published-cat',
                                  })

    def test___search___q_param_anonymous_search_with_param(self):
        self.indexSomePrivateRecords()
        recs, _ = self.search('dataset', None, {'q': ['"cat"'], 'datahub.ownerid': ['"owner1"']})
        self.assertEquals(len(recs), 1)
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'owner1-published-cat'})

    def test___search___q_param_authenticated_search(self):
        self.indexSomePrivateRecords()
        recs, _ = self.search('dataset', 'owner1', {'q': ['"cat"']})
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'owner1-published-cat',
                                  'owner1-else-cat',
                                  'owner2-published-cat',
                                  })
        self.assertEquals(len(recs), 3)

    def test___search___q_param_with_similar_param(self):
        self.indexSomeRecordsToTestMapping()
        recs, _ = self.search('dataset', None, {'q': ['"test2"']})
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'package-id-2'})
        self.assertEquals(len(recs), 1)

        recs, _ = self.search('dataset', None, {'q': ['"dataset"'], 'datahub.owner': ['"BlaBla2@test2.com"']})
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'package-id-2'})
        self.assertEquals(len(recs), 1)

        recs, _ = self.search('dataset', None, {'datahub.owner': ['"BlaBla2@test2.com"']})
        ids = set([r['name'] for r in recs])
        self.assertSetEqual(ids, {'package-id-2'})
        self.assertEquals(len(recs), 1)

    def test_search__q_param_in_readme(self):
        body = {
            'name': True,
            'title': 'testing',
            'license': 'str',
            'datahub': {
                'name': 'innername',
                'findability': 'published',
                'stats': {
                    'bytes': 10
                }
            },
            'readme': 'text only in README',
            'not_readme': 'NOTREADME'
        }
        self.es.index('datahub', 'dataset', body)
        self.es.indices.flush('datahub')
        recs, _ = self.search('dataset', None, {'q': ['"README"']})
        self.assertEquals(len(recs), 1)
        ## Make sure not queries unlisted fields
        recs, _ = self.search('dataset', None, {'q': ['"NOTREADME"']})
        self.assertEquals(len(recs), 0)
