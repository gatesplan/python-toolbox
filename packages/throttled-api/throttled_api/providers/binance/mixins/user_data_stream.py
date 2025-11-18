"""
User Data Stream Endpoints Mixin
"""


class UserDataStreamMixin:
    """
    User Data Stream endpoints for WebSocket listen key management
    """

    async def create_listen_key(self) -> dict:
        """
        Create a listen key for user data stream

        POST /api/v3/userDataStream
        Weight: 2

        Returns:
            {"listenKey": "..."}
        """
        await self._check_and_wait(2)
        return self.client.create_listen_key()

    async def keep_alive_listen_key(self, listen_key: str) -> dict:
        """
        Keep alive a listen key (extends validity by 60 minutes)

        PUT /api/v3/userDataStream
        Weight: 2

        Args:
            listen_key: Listen key to keep alive

        Returns:
            Empty dict on success
        """
        await self._check_and_wait(2)
        return self.client.keep_alive_listen_key(listenKey=listen_key)

    async def close_listen_key(self, listen_key: str) -> dict:
        """
        Close a listen key

        DELETE /api/v3/userDataStream
        Weight: 2

        Args:
            listen_key: Listen key to close

        Returns:
            Empty dict on success
        """
        await self._check_and_wait(2)
        return self.client.close_listen_key(listenKey=listen_key)
