"""
Unittests for `tcpnetlock.server` package.
"""
from tcpnetlock.server.action import Action


class TestActions:

    def test_valid_single_action(self):
        action = Action.from_line('lock1')
        assert action.name == 'lock1'

    def test_valid_action_with_one_param(self):
        action = Action.from_line('lock1,blocking:true')
        assert action.name == 'lock1'
        assert len(action.params) == 1
        assert action.params.get('blocking') == 'true'

    def test_valid_action_with_two_param(self):
        action = Action.from_line('lock1,blocking:true,foo:bar')
        assert action.name == 'lock1'
        assert len(action.params) == 2
        assert action.params.get('blocking') == 'true'
        assert action.params.get('foo') == 'bar'

    def test_valid_action_param_without_value(self):
        action = Action.from_line('lock1,blocking')
        assert action.name == 'lock1'
        assert len(action.params) == 1
        assert action.params.get('blocking') == ''

    def test_empty_action_fails(self):
        action = Action.from_line(',param:value')
        assert action
        assert not action.is_valid()

    def test_empty_param_fails(self):
        action = Action.from_line('action,:value')
        assert action
        assert not action.is_valid()
