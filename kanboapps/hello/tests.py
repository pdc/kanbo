# -*-coding: UTF-8-*-

import re
from mock import Mock, call
from django.test import TestCase
from django.contrib.auth.models import User
from kanboapps.hello.pipeline import get_username, username_rejected


class GetUserTests(TestCase):
    def setUp(self):
        pass

    def test_it_uses_existing_user_if_supplied(self):
        user = User.objects.create(username='bantha69')
        result = get_username({}, user)

        self.assertEqual('bantha69', result['username'])

    def test_it_uses_proffered_username(self):
        result = get_username({'username': 'smarfpon3'}, user_exists=lambda u: False)

        self.assertEqual('smarfpon3', result['username'])

    def test_it_slugifies_proffered_username(self):
        result = get_username({'username': 'Mister Apple Cheeks'}, user_exists=lambda u: False)

        self.assertEqual('mister-apple-cheeks', result['username'])

    def test_it_shortens_proffered_username(self):
        result = get_username({'username': 'long name more than thirty characters which seems to be the defauilt maximum user length'}, user_exists=lambda u: False)

        self.assertEqual('long-name-more-than-thirty-cha', result['username'])

    def test_it_randomizes_names_If_collision(self):
        mock_func = Mock('func')
        mock_func.side_effect = [True, False]
        result = get_username({'username': 'yar'}, user_exists=mock_func)

        self.assertEqual('yar', result['username'][:3])
        self.assertTrue(re.match('[a-f0-9]{16}', result['username'][3:]))

        # Check it called the exists function twice.
        self.assertEqual(2, len(mock_func.call_args_list))
        self.assertEqual(call('yar'), mock_func.call_args_list[0])
        self.assertEqual(call(result['username']), mock_func.call_args_list[1])

    def test_asciification_drops_accents(self):
        result = get_username({'username': 'zoë'}, user_exists=lambda u: False)

        self.assertEqual('zoe', result['username'])

    def test_it_mangles_lukasz_as_little_as_possible(self):
        # Most special letters get handled by the decompositoon step,
        # but the Polish Ł has no decomposition info.
        result = get_username({'username': u'ŁukaszKorecki'}, user_exists=lambda u: False)

        self.assertEqual('lukaszkorecki', result['username'])

    def test_random_nantional_characters(self):
        result = get_username({'username': u'æÆßøØœŒåÅĳ'})

        self.assertEqual('aeaessoooeoeaaij', result['username'])




class UserExistsTests(TestCase):
    def setUp(self):
        for name in ['alice', 'bob', 'eve']:
            User.objects.create(username=name)

    def test_it_rejects_existing_user_name(self):
        self.assertTrue(username_rejected('alice'))

    def test_it_accepts_nonexisting_user_name(self):
        self.assertFalse(username_rejected('hermione'))

    def test_it_rejects_numbers(self):
        self.assertTrue(username_rejected('42'))
        self.assertTrue(username_rejected('-1'))

    def test_it_rejects_url_prefixes(self):
        for name in ['about', 'hello', 'boards']:
            self.assertTrue(username_rejected(name),
                    u'Expected \'{0}\' to be rejected'.format(name))

    def test_it_rejects_empty_names(self):
        for name in [None, '']:
            self.assertTrue(username_rejected(name),
                    u'Expected \'{0!r}\' to be rejected'.format(name))

