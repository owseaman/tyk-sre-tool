import unittest
import socket
import requests

from unittest.mock import MagicMock, patch
from socketserver import TCPServer
from threading import Thread
from kubernetes import client
from kubernetes.client.models import (
    VersionInfo,
    V1DeploymentList,
    V1Deployment,
    V1DeploymentStatus,
    V1DeploymentSpec,
    V1ObjectMeta,
)

from app import app


class TestGetKubernetesVersion(unittest.TestCase):
    def test_good_version(self):
        api_client = client.ApiClient()

        version = VersionInfo(
            build_date="",
            compiler="",
            git_commit="",
            git_tree_state="fake",
            git_version="1.25.0-fake",
            go_version="",
            major="1",
            minor="25",
            platform=""
        )
        api_client.call_api = MagicMock(return_value=version)

        version = app.get_kubernetes_version(api_client)
        self.assertEqual(version, "1.25.0-fake")

    def test_exception(self):
        api_client = client.ApiClient()
        api_client.call_api = MagicMock(side_effect=ValueError("test"))

        with self.assertRaisesRegex(ValueError, "test"):
            app.get_kubernetes_version(api_client)


class TestAppHandler(unittest.TestCase):
    def setUp(self):
        super().setUp()

        port = self._get_free_port()
        self.mock_server = TCPServer(("localhost", port), app.AppHandler)

        # Run the mock TCP server with AppHandler on a separate thread to avoid blocking the tests.
        self.mock_server_thread = Thread(target=self.mock_server.serve_forever)
        self.mock_server_thread.daemon = True
        self.mock_server_thread.start()

    def _get_free_port(self):
        """Returns a free port number from OS"""
        s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
        s.bind(("localhost", 0))
        __, port = s.getsockname()
        s.close()

        return port

    def _get_url(self, target):
        """Returns a URL to pass into the requests so that they reach this suite's mock server"""
        host, port = self.mock_server.server_address
        return f"http://{host}:{port}/{target}"

    def test_healthz_ok(self):
        resp = requests.get(self._get_url("healthz"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, "ok")

    @patch('kubernetes.client.AppsV1Api')
    def test_deployments_health(self, mock_apps_v1_api):
        # Mock deployment data
        deployment = V1Deployment(
            metadata=V1ObjectMeta(name="test-dep", namespace="default"),
            spec=V1DeploymentSpec(
                replicas=3,
                selector={'matchLabels': {'app': 'test'}},  # Add required selector
                template={
                    'metadata': {'labels': {'app': 'test'}},
                    'spec': {
                        'containers': [{
                            'name': 'test',
                            'image': 'nginx:latest'
                        }]
                    }
                }
            ),
            status=V1DeploymentStatus(available_replicas=3)
        )
        mock_apps_v1_api.return_value.list_deployment_for_all_namespaces.return_value = \
            V1DeploymentList(items=[deployment])

        # Test the endpoint
        resp = requests.get(self._get_url("api/deployments/health"))
        self.assertEqual(resp.status_code, 200)
        
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "test-dep")
        self.assertEqual(data[0]["namespace"], "default")
        self.assertEqual(data[0]["desired_replicas"], 3)
        self.assertEqual(data[0]["available_replicas"], 3)
        self.assertTrue(data[0]["healthy"])

    @patch('kubernetes.client.NetworkingV1Api')
    def test_create_network_policy(self, mock_networking_v1_api):
        # Test data
        policy_data = {
            "name": "test-policy",
            "namespace": "default",
            "source_labels": {"app": "source"},
            "destination_labels": {"app": "destination"}
        }

        # Mock API response
        mock_response = MagicMock()
        mock_response.metadata.name = "test-policy"
        mock_response.metadata.namespace = "default"
        mock_networking_v1_api.return_value.create_namespaced_network_policy.return_value = mock_response

        # Test the endpoint
        resp = requests.post(
            self._get_url("api/network-policy"),
            json=policy_data
        )
        
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["status"], "created")
        self.assertEqual(data["name"], "test-policy")
        self.assertEqual(data["namespace"], "default")         


if __name__ == '__main__':
    unittest.main()
