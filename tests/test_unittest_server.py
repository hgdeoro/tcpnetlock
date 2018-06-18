"""
Unittests for `tcpnetlock.server` package.
"""
import tcpnetlock.action
from tcpnetlock import server


def test_valid_single_action():
    action = tcpnetlock.action.Action.from_line('lock1')
    assert action.name == 'lock1'


def test_valid_action_with_one_param():
    action = tcpnetlock.action.Action.from_line('lock1,blocking:true')
    assert action.name == 'lock1'
    assert len(action.params) == 1
    assert action.params.get('blocking') == 'true'


def test_valid_action_with_two_param():
    action = tcpnetlock.action.Action.from_line('lock1,blocking:true,foo:bar')
    assert action.name == 'lock1'
    assert len(action.params) == 2
    assert action.params.get('blocking') == 'true'
    assert action.params.get('foo') == 'bar'


def test_valid_action_param_without_value():
    action = tcpnetlock.action.Action.from_line('lock1,blocking')
    assert action.name == 'lock1'
    assert len(action.params) == 1
    assert action.params.get('blocking') == ''
