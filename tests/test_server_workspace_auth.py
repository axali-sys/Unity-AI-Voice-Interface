import json
import os
import unittest
from unittest.mock import patch
from xparallel import server

class AuthenticatedWorkspaceTests(unittest.TestCase):
    def test_workspace_token_overrides_caller_workspace_and_role(self):
        handler=object.__new__(server.Handler)
        handler.headers={"Authorization":"Bearer tenant-secret"}
        with patch.dict(os.environ,{"XP_WORKSPACE_TOKENS_JSON":json.dumps({"tenant-a":{"token":"tenant-secret","role":"operator"}}),"XP_DEFAULT_WORKSPACE_ID":"default"},clear=True), patch.object(server,"TOKEN","global-admin-secret"):
            self.assertTrue(handler.authorized())
            self.assertEqual(handler.role(),"operator")
            context=handler.authenticated_context({"workspace_id":"tenant-b","actor":"spoofed"})
        self.assertEqual(context["workspace_id"],"tenant-a")
        self.assertEqual(context["actor"],"workspace-token")

    def test_unknown_workspace_token_is_not_authorized(self):
        handler=object.__new__(server.Handler)
        handler.headers={"Authorization":"Bearer wrong"}
        with patch.dict(os.environ,{"XP_WORKSPACE_TOKENS_JSON":json.dumps({"tenant-a":{"token":"tenant-secret","role":"owner"}})},clear=True), patch.object(server,"TOKEN",None):
            self.assertFalse(handler.authorized())
            self.assertEqual(handler.role(),"viewer")

if __name__=="__main__":
    unittest.main()
