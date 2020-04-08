#
# Серверное приложение для соединений
#
import asyncio
import time
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                for user in self.server.clients:
                    if user.login == login:
                        self.transport.write(f"Логин {login} занят, попробуйте другой.\n".encode())
                        # time.sleep(5)
                        self.transport.close()
                        return
                self.login = login
                self.transport.write(f"Привет, {login}!\n".encode())
                self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}"

        if len(self.server.history) >= 10:
            del self.server.history[0]
        self.server.history.append(message)

        for user in self.server.clients:
            user.transport.write(f"{message}\n".encode())

    def send_history(self):
        message = ''.join(map(str, self.server.history))
        num = len(self.server.history)
        self.transport.write(f"\nПоследние {num} сообщений:\n{message}\n".encode())

class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
