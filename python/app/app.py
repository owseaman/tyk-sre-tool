import socketserver
import json
from kubernetes import client
from http.server import BaseHTTPRequestHandler


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Catch all incoming GET requests"""
        if self.path == "/healthz":
            self.healthz()
        elif self.path == "/api/deployments/health":
            self.deployments_health()  # New endpoint for deployment health    
        else:
            self.send_error(404)

    def deployments_health(self):
        """Responds with the health status of all deployments"""
        try:
            api = client.AppsV1Api()
            deployments = api.list_deployment_for_all_namespaces(watch=False)
            health_status = []
            for deployment in deployments.items:
                desired_replicas = deployment.spec.replicas
                available_replicas = deployment.status.available_replicas if deployment.status.available_replicas is not None else 0
                health_status.append({
                    "namespace": deployment.metadata.namespace,
                    "name": deployment.metadata.name,
                    "desired_replicas": desired_replicas,
                    "available_replicas": available_replicas,
                    "healthy": desired_replicas == available_replicas
                })
            self.respond(200, json.dumps(health_status))
        except Exception as e:
            self.respond(500, str(e))        

    def healthz(self):
        """Responds with the health status of the application"""
        self.respond(200, "ok")

    def respond(self, status: int, content: str):
        """Writes content and status code to the response socket"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

        self.wfile.write(bytes(content, "UTF-8"))

    def do_POST(self):
        """Handle POST requests for network policies"""
        if self.path == "/api/network-policy":
            self.create_network_policy()  # New endpoint for creating network policies
        else:
            self.send_error(404)
            
    def create_network_policy(self):
        """Create a network policy to block traffic between workloads"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            policy_spec = json.loads(post_data.decode('utf-8'))
            name = policy_spec.get('name')
            namespace = policy_spec.get('namespace')
            source_labels = policy_spec.get('source_labels')
            destination_labels = policy_spec.get('destination_labels')
            
            # Create the network policy using the Kubernetes API
            networking_v1 = client.NetworkingV1Api()
            policy = client.V1NetworkPolicy(
                metadata=client.V1ObjectMeta(name=name, namespace=namespace),
                spec=client.V1NetworkPolicySpec(
                    pod_selector=client.V1LabelSelector(match_labels=destination_labels),
                    ingress=[
                        client.V1NetworkPolicyIngressRule(
                            _from=[
                                client.V1NetworkPolicyPeer(
                                    pod_selector=client.V1LabelSelector(match_labels=source_labels)
                                )
                            ]
                        )
                    ],
                    policy_types=["Ingress"]
                )
            )
            result = networking_v1.create_namespaced_network_policy(namespace=namespace, body=policy)
            self.respond(201, json.dumps({"status": "created", "name": result.metadata.name, "namespace": result.metadata.namespace}))
        except Exception as e:
            self.respond(400, str(e))

    def api_status(self):
        """Return detailed API connection status"""
        try:
            version = get_kubernetes_version(client.ApiClient())
            self.respond(200, json.dumps({"connected": True, "version": version}))
        except Exception as e:
            self.respond(500, json.dumps({"connected": False, "error": str(e)}))
        

def get_kubernetes_version(api_client: client.ApiClient) -> str:
    """
    Returns a string GitVersion of the Kubernetes server defined by the api_client.

    If it can't connect an underlying exception will be thrown.
    """
    version = client.VersionApi(api_client).get_code()
    return version.git_version


def start_server(address):
    """
    Launches an HTTP server with handlers defined by AppHandler class and blocks until it's terminated.

    Expects an address in the format of `host:port` to bind to.

    Throws an underlying exception in case of error.
    """
    try:
        host, port = address.split(":")
    except ValueError:
        print("invalid server address format")
        return

    with socketserver.TCPServer((host, int(port)), AppHandler) as httpd:
        print("Server listening on {}".format(address))
        httpd.serve_forever()
