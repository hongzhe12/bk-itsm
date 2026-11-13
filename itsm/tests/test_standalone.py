import json
from types import SimpleNamespace
from unittest import mock

from django.test import RequestFactory, SimpleTestCase, override_settings

from itsm.auth_iam.utils import IamRequest
from itsm.component.utils.client_backend_query import get_all_apps
from itsm.role.models import UserRole


@override_settings(STANDALONE_MODE=True)
class StandaloneBoundaryTest(SimpleTestCase):
    def test_iam_resource_actions_are_allowed(self):
        permissions = IamRequest(username="admin").resource_multi_actions_allowed(
            ["project_view", "ticket_management"], []
        )

        self.assertEqual(
            permissions,
            {"project_view": True, "ticket_management": True},
        )

    def test_iam_batch_resource_actions_are_allowed(self):
        permissions = IamRequest(username="admin").batch_resource_multi_actions_allowed(
            ["ticket_view"],
            [{"resource_id": "1", "resource_type": "service"}],
        )

        self.assertEqual(permissions, {"1": {"ticket_view": True}})

    @mock.patch("itsm.component.utils.client_backend_query.CMDBApi.get_client")
    def test_cmdb_is_not_called(self, get_client):
        self.assertEqual(get_all_apps(), [])
        get_client.assert_not_called()

    @mock.patch("itsm.role.models.CMDBApi.get_client")
    def test_cmdb_roles_are_empty(self, get_client):
        self.assertEqual(UserRole.get_cmdb_role_by_user("admin"), {})
        get_client.assert_not_called()

    def test_apigw_calls_are_disabled(self):
        from itsm.component.apigw.client.backend_apigateway import BkApigwComponent

        self.assertEqual(
            BkApigwComponent().http({}),
            {"result": True, "code": "OK", "message": "success", "data": []},
        )

    def test_sops_and_devops_components_are_disabled(self):
        from itsm.pipeline_plugins.components.collections.bk_devops import BkDevOpsService
        from itsm.pipeline_plugins.components.collections.bk_sops import BkOpsService

        self.assertFalse(BkOpsService(name="sops").execute(None, None))
        self.assertFalse(BkOpsService(name="sops").schedule(None, None))
        self.assertFalse(BkDevOpsService(name="devops").execute(None, None))
        self.assertFalse(BkDevOpsService(name="devops").schedule(None, None))

    def test_unauthenticated_xhr_gets_login_url(self):
        from common.standalone import login_required

        request = RequestFactory().get(
            "/init/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        request.user = SimpleNamespace(is_authenticated=False)

        response = login_required(lambda req: None)(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.content)["login_url"], "/login/")

    def test_index_redirects_to_frontend(self):
        from itsm.sites.views import index

        response = index(RequestFactory().get("/"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://127.0.0.1:8004/")

    def test_worker_beat_args_are_split(self):
        from itsm.helper.management.commands.celery import split_worker_beat_args

        worker_args, beat_args = split_worker_beat_args(
            ["worker", "-l", "info", "-B"]
        )

        self.assertEqual(worker_args, ["worker", "-l", "info", "--pool", "solo"])
        self.assertEqual(
            beat_args,
            [
                "beat",
                "-l",
                "info",
                "--scheduler",
                "django_celery_beat.schedulers:DatabaseScheduler",
            ],
        )

    def test_worker_keeps_explicit_pool(self):
        from itsm.helper.management.commands.celery import split_worker_beat_args

        worker_args, _ = split_worker_beat_args(
            ["worker", "-l", "info", "-B", "-P", "threads"]
        )

        self.assertEqual(worker_args, ["worker", "-l", "info", "-P", "threads"])
