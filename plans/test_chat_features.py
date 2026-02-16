import pytest
from channels.testing import WebsocketCommunicator
from tripvo_backend.asgi_channels import application

@pytest.mark.asyncio
async def test_chat_text_message():
    communicator = WebsocketCommunicator(application, "/ws/chat/testplan/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to({
        "type": "message",
        "user": "tester",
        "content": "Hello world!"
    })
    response = await communicator.receive_json_from()
    assert response["type"] == "message"
    assert response["message"]["content"] == "Hello world!"
    await communicator.disconnect()

@pytest.mark.asyncio
async def test_chat_image_upload():
    communicator = WebsocketCommunicator(application, "/ws/chat/testplan/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to({
        "type": "image",
        "user": "tester",
        "content": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
        "filename": "test.png"
    })
    response = await communicator.receive_json_from()
    assert response["type"] == "message"
    assert response["message"]["filename"] == "test.png"
    await communicator.disconnect()

@pytest.mark.asyncio
async def test_chat_reaction():
    communicator = WebsocketCommunicator(application, "/ws/chat/testplan/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to({
        "type": "reaction",
        "user": "tester",
        "msgIdx": 0,
        "reaction": "👍"
    })
    response = await communicator.receive_json_from()
    assert response["type"] == "reaction"
    assert response["reaction"] == "👍"
    await communicator.disconnect()
