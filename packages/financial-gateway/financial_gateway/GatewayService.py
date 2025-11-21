import os
from typing import Dict, Optional
from dotenv import load_dotenv
from simple_logger import init_logging, func_logging, logger
from binance.spot import Spot as BinanceClient

from financial_gateway.gateways.base import BaseGateway
from financial_gateway.gateways.binance_spot import BinanceSpotGateway
from financial_gateway.gateways.upbit_spot import UpbitSpotGateway
from throttled_api.providers.binance import BinanceSpotThrottler
from throttled_api.providers.upbit import UpbitSpotThrottler
from throttled_api.providers.upbit.UpbitClientAdapter import UpbitClientAdapter


class GatewayService:
    # Gateway 팩토리 및 인스턴스 관리

    @init_logging(level="INFO", log_params=True)
    def __init__(self, config: Optional[Dict] = None):
        self._gateways: Dict[str, BaseGateway] = {}
        self._config = config or {}

    @classmethod
    @func_logging(level="INFO")
    def from_env(cls, env_file: Optional[str] = None) -> "GatewayService":
        # 환경변수에서 API 키 자동 로드
        load_dotenv(env_file)

        config = {}

        # Binance 설정
        binance_testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"

        if binance_testnet:
            binance_key = os.getenv("BINANCE_TESTNET_API_KEY")
            binance_secret = os.getenv("BINANCE_TESTNET_API_SECRET")
        else:
            binance_key = os.getenv("BINANCE_SPOT_API_KEY")
            binance_secret = os.getenv("BINANCE_SPOT_API_SECRET")

        if binance_key and binance_secret:
            config["binance_spot"] = {
                "api_key": binance_key,
                "api_secret": binance_secret,
                "testnet": binance_testnet
            }
            logger.info(f"Binance API keys loaded (testnet={binance_testnet})")
        else:
            logger.warning("Binance API keys not found in environment")

        # Upbit 설정
        upbit_access = os.getenv("UPBIT_ACCESS_KEY")
        upbit_secret = os.getenv("UPBIT_SECRET_KEY")

        if upbit_access and upbit_secret:
            config["upbit_spot"] = {
                "access_key": upbit_access,
                "secret_key": upbit_secret
            }
            logger.info("Upbit API keys loaded")
        else:
            logger.warning("Upbit API keys not found in environment")

        return cls(config)

    @func_logging(level="INFO", log_params=True)
    def get(self, gateway_name: str) -> BaseGateway:
        # Gateway 획득 (캐시 우선, 없으면 생성)
        if gateway_name in self._gateways:
            logger.debug(f"Returning cached gateway: {gateway_name}")
            return self._gateways[gateway_name]

        logger.info(f"Creating new gateway: {gateway_name}")
        gateway = self._create_gateway(gateway_name)
        self._gateways[gateway_name] = gateway
        return gateway

    def _create_gateway(self, gateway_name: str) -> BaseGateway:
        # Gateway 생성 팩토리 메서드
        if gateway_name not in self._config:
            raise ValueError(
                f"Gateway '{gateway_name}' not configured. "
                f"Available: {list(self._config.keys())}"
            )

        config = self._config[gateway_name]

        if gateway_name == "binance_spot":
            return self._create_binance_spot(config)
        elif gateway_name == "upbit_spot":
            return self._create_upbit_spot(config)
        else:
            raise ValueError(f"Unknown gateway type: {gateway_name}")

    @func_logging(level="INFO")
    def _create_binance_spot(self, config: Dict) -> BinanceSpotGateway:
        # BinanceSpotGateway 생성
        api_key = config["api_key"]
        api_secret = config["api_secret"]
        testnet = config.get("testnet", False)

        # Binance API 클라이언트 생성
        if testnet:
            client = BinanceClient(
                api_key=api_key,
                api_secret=api_secret,
                base_url="https://testnet.binance.vision"
            )
            logger.info("Binance Testnet client created")
        else:
            client = BinanceClient(
                api_key=api_key,
                api_secret=api_secret
            )
            logger.info("Binance Production client created")

        # Throttler 생성 (client 전달)
        throttler = BinanceSpotThrottler(client=client)

        return BinanceSpotGateway(throttler)

    @func_logging(level="INFO")
    def _create_upbit_spot(self, config: Dict) -> UpbitSpotGateway:
        # UpbitSpotGateway 생성
        access_key = config["access_key"]
        secret_key = config["secret_key"]

        # Upbit API 클라이언트 어댑터 생성
        client = UpbitClientAdapter(access_key=access_key, secret_key=secret_key)
        logger.info("Upbit client adapter created")

        # Throttler 생성 (client 전달)
        throttler = UpbitSpotThrottler(client=client)

        return UpbitSpotGateway(throttler)
