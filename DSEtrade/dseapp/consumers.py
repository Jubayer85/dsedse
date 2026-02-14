from channels.generic.websocket import AsyncWebsocketConsumer
import json
from dseapp.signals.smc_engine import SMCSignalEngine

class SignalConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        candles = data["candles"]

        engine = SMCSignalEngine(candles)
        result = engine.analyze()

        await self.send(text_data=json.dumps(result))