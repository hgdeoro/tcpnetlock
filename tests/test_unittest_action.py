"""
Unittests for `tcpnetlock.server.action` package.
"""

from tcpnetlock.server import action


class TestActionStr:
    """
    Test Action.__str__() do not fails
    """

    def test_action_str(self):
        act = action.Action.from_line('action_name')
        assert act.is_valid()
        str(act)

    def test_action_str_invalid_action(self):
        act = action.Action.from_line(',no:action')
        assert not act.is_valid()
        str(act)

    def test_action_str_with_params(self):
        act = action.Action.from_line('action_name,key1:value1')
        assert act.is_valid()
        str(act)

    def test_action_str_with_params_invalid_action(self):
        act = action.Action.from_line('action_name,:nokey')
        assert not act.is_valid()
        str(act)
