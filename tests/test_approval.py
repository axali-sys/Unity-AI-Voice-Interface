import unittest
from xparallel.approval import consume_approval, issue_approval

class ApprovalTicketTests(unittest.TestCase):
    def test_ticket_is_bound_to_action_payload_workspace_and_actor(self):
        ticket=issue_approval(plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"YQ=="}},
                              workspace_id="alpha",actor="authenticated-token-holder")["approval_ticket"]
        self.assertFalse(consume_approval(ticket,plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"Yg=="}},
                                          workspace_id="alpha",actor="authenticated-token-holder"))
        # Tickets are one-time, including failed attempts.
        self.assertFalse(consume_approval(ticket,plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"YQ=="}},
                                          workspace_id="alpha",actor="authenticated-token-holder"))

    def test_ticket_is_single_use_and_workspace_bound(self):
        ticket=issue_approval(plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"YQ=="}},
                              workspace_id="alpha",actor="authenticated-token-holder")["approval_ticket"]
        self.assertFalse(consume_approval(ticket,plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"YQ=="}},
                                          workspace_id="beta",actor="authenticated-token-holder"))
        ticket2=issue_approval(plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"YQ=="}},
                               workspace_id="alpha",actor="authenticated-token-holder")["approval_ticket"]
        self.assertTrue(consume_approval(ticket2,plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"YQ=="}},
                                         workspace_id="alpha",actor="authenticated-token-holder"))
        self.assertFalse(consume_approval(ticket2,plugin_id="xparallel_sandbox",action="run_tests",payload={"files":{"a.py":"YQ=="}},
                                          workspace_id="alpha",actor="authenticated-token-holder"))

if __name__ == "__main__":
    unittest.main()
