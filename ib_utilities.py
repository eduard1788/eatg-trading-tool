from ib_insync import IB, util
from common import accounts
import asyncio

# This must live in another central place


class IBKRApiConn:
    def __init__(self, user: str):
        self.ib = IB()
        self.user = user
        self.account = accounts[user]['acc']
        self.conn_port = accounts[user]['conn_port'][0]
        self.client_id = accounts[user]['client_id'][0]

    def ib_connect(self):
        if not self.ib.isConnected():
            try:
                print(f"Connecting for user: {self.user}")
                self.ib.connect(
                    '127.0.0.1',
                    self.conn_port,
                    self.client_id
                )
                # self.ib.run() ---> This stalls the program
                print(f"Connected successfully for account(s): {self.account}")
            except Exception as error:
                print(f"Error while trying to connect. Error: {error}")
        else:
            print("You are already connected")

    def ib_disconnect(self):
        if self.ib.isConnected():
            try:
                print(f"Disconnecting for user: {self.user}")
                self.ib.disconnect()
                print(f"Disconnected successfully for account(s): {self.account}")
            except Exception as error:
                print(f"Error while trying to disconnect. Error: {error}")
        else:
            print("You are already disconnected")

#if __name__ == "__main__":
    # util.startLoop()
    #client = IBKRApiConn('eduardo')
    #client.ib_disconnect()

    #print("Connection active. Waiting for events...")
    #client.ib.run()