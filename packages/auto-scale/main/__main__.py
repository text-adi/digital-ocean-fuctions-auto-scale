import asyncio
import base64
import os
from datetime import datetime

import aiohttp
import yaml
from kubernetes import client, config

API_KEY = os.getenv('API_KEY')
base64_string = os.getenv('K8S_CONFIG_BASE64')

decoded_bytes = base64.b64decode(base64_string)
decoded_string = decoded_bytes.decode("utf-8")

yaml_dict = yaml.safe_load(decoded_string)

config.load_kube_config_from_dict(yaml_dict)


class AutoScale:

    def __init__(self, api_key: str, service_name: str, namespace: str, lb_urn: str):
        self.API_KEY = api_key

        self.service_name = service_name
        self.namespace = namespace

        if lb_urn is None:
            raise ValueError("Передайте urn для load balancer будь ласка, хоча б")
        self.lb_urn = lb_urn

    def edit_size_unit(self, size: int):
        """Змінювання кількості unit для load balancing"""
        v1 = client.CoreV1Api()
        service = v1.read_namespaced_service(name=self.service_name, namespace=self.namespace)
        param = 'service.beta.kubernetes.io/do-loadbalancer-size-unit'
        if service.metadata.annotations[param] == str(size):
            print("Поточне значення дорівнює бажаному. Нічого не робимо")
            return

        service.metadata.annotations[param] = str(size)
        try:
            updated_service = v1.patch_namespaced_service(
                name=self.service_name, namespace=self.namespace, body=service
            )
            print("Сервіс успішно оновлено:", updated_service.metadata.name, )
            print("Поточне значення:", service.metadata.annotations[param])
        except client.exceptions.ApiException as e:
            print("Не вдалося змінити значення. Причина:", e)

    async def _get_result(self, endpoint: str, ts):
        url = f"https://api.digitalocean.com/v2/monitoring/metrics/load_balancer/{endpoint}?lb_id={self.lb_urn}&start={ts}&end={ts}"
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 401:
                    raise ConnectionError(f"Помилка авторизації - {await response.json()}")

                data = await response.json()

                value = data['data']['result'][0]['values'][0][1]
                return value

    async def get_current_limit(self, ts):
        return await self._get_result(
            endpoint="frontend_connections_limit",
            ts=ts,
        )

    async def get_current_connection(self, ts):
        return await self._get_result(
            endpoint="frontend_connections_current",
            ts=ts,
        )


async def run_async(args):
    alert_percent = float(args.get('alert_percent', 80))
    lb_urn = args.get('lb_urn')

    max_size_unit = int(args.get('max_size_unit', 10))
    min_size_unit = int(args.get('min_size_unit', 1))

    print(
        "Поточна конфігурація:",
        f"alert_percent - {alert_percent}",
        f"max_size_unit - {max_size_unit}",
        f"min_size_unit - {min_size_unit}",
    )

    service_name = args.get('service_name', 'ingress-nginx-controller')
    namespace = args.get('namespace', 'ingress-nginx')

    dt = datetime.now()
    ts = datetime.timestamp(dt)

    auto_scale = AutoScale(
        api_key=API_KEY, service_name=service_name, namespace=namespace, lb_urn=lb_urn
    )
    tasks = [
        auto_scale.get_current_limit(ts),
        auto_scale.get_current_connection(ts)
    ]
    result = await asyncio.gather(*tasks, return_exceptions=False)
    current_limit = float(result[0])
    current_connection = float(result[1])

    if current_connection / current_limit > alert_percent:
        print("Alert!!! Need up to", max_size_unit)
        auto_scale.edit_size_unit(max_size_unit)
    else:
        print("Relax:). Size down to", min_size_unit)
        auto_scale.edit_size_unit(min_size_unit)


def main(args):
    asyncio.run(run_async(args))
