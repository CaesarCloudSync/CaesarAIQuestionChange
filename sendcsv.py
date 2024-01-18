import websockets
import asyncio
import json
import base64
# The main function that will handle connection and communication
# with the server
with open("statements.csv","rb") as f:
    csvdata = f.read()
async def ws_client():
    print("WebSocket: Client Connected.")
    url = "ws://127.0.0.1:9000/changetoquestioncsvws"
    # Connect to the server
    async with websockets.connect(url) as ws:
        # Send values to the server
        print(base64.b64encode(csvdata).decode()[:30])
        await ws.send(json.dumps({"file":base64.b64encode(csvdata).decode()}))
  
 
        # Stay alive forever, listen to incoming msgs
        while True:
            msg = await ws.recv()
            print(msg)
 
# Start the connection
asyncio.run(ws_client())