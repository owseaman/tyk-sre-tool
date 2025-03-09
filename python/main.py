import sys
import argparse

from kubernetes import client, config
from app import AppHandler, start_server, get_kubernetes_version

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tyk SRE Assignment",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-k", "--kubeconfig", type=str, default="",
                        help="path to kubeconfig, leave empty for in-cluster")
    parser.add_argument("-a", "--address", type=str, default=":8080",
                        help="HTTP server listen address")
    args = parser.parse_args()

    # if args.kubeconfig != "":
    #     config.load_kube_config(config_file=args.kubeconfig)
    # else:
    #     config.load_incluster_config()

    try:
        # If kubeconfig is provided, use it (local development)
        if args.kubeconfig:
            config.load_kube_config(config_file=args.kubeconfig)
        # Otherwise, try in-cluster config (running in Kubernetes)
        else:
            config.load_incluster_config()
    except Exception as e:
        print(f"Failed to load Kubernetes configuration: {e}")
        sys.exit(1)

    api_client = client.ApiClient()

    try:
        version = get_kubernetes_version(api_client)
        print("Connected to Kubernetes {}".format(version))
    except Exception as e:
        print("Failed to connect to Kubernetes: {}".format(e))
        sys.exit(1)

    print("Connected to Kubernetes {}".format(version))

    try:
        start_server(args.address)
    except KeyboardInterrupt:
        print("Server terminated")
