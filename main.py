import os
import re
from typing import Dict
from fastapi import FastAPI, Request, HTTPException
from azure.communication.sms import SmsClient
from azure.communication.callautomation import CallAutomationClient, CallInvite, SsmlSource
from azure.communication.identity import PhoneNumberIdentifier
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = FastAPI()

# Configuration
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
ACS_CALLBACK_URL = os.getenv("ACS_CALLBACK_URL", "https://yourdomain.com/events")
ACS_SOURCE_PHONE_NUMBER = os.getenv("ACS_SOURCE_PHONE_NUMBER", "+1234567890")
ACS_COGNITIVE_SERVICES_ENDPOINT = os.getenv("ACS_COGNITIVE_SERVICES_ENDPOINT")
ACS_SENDER_ID = os.getenv("ACS_SENDER_ID", "MFA")
SECRET_HEADER = os.getenv("SECRET_HEADER", "myS3cr3t$k3y")

sms_client = SmsClient.from_connection_string(ACS_CONNECTION_STRING)
call_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)
pending_calls: Dict[str, Dict[str, str]] = {}

@app.post("/send-text-code")
async def send_text_message(request: Request):
    # auth = request.headers.get("Authorization") or request.headers.get("authorization")
    # if auth != SECRET_HEADER:
    #     raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    print("Received SMS request body:", body)

    msg = body["data"]["messageProfile"]["msgTemplate"]
    phone_number = body["data"]["messageProfile"].get("phoneNumber")
    if not phone_number:
        raise ValueError("Missing phoneNumber in request")

    phone_number = re.sub(r"[^\d+]", "", phone_number)
    if not phone_number.startswith("+"):
        phone_number = f"+34{phone_number}"

    print(f"Sending SMS from: '{ACS_SENDER_ID}' to: '{phone_number}' with message: '{msg}'")

    sms_client.send(
        from_=ACS_SENDER_ID,
        to=[phone_number],
        message=msg,
        enable_delivery_report=True
    )

    return {"status": "SMS successfully sent"}

@app.post("/send-voice-code")
async def send_voice_message(request: Request):
    # auth = request.headers.get("Authorization") or request.headers.get("authorization")
    # if auth != SECRET_HEADER:
    #     raise HTTPException(status_code=401, detail="Unauthorized")

    payload = await request.json()
    print("Received /send-voice-code payload:", payload)
    # Support both direct and nested shapes
    raw_number = payload.get("phoneNumber") or payload.get("data", {}).get("messageProfile", {}).get("phoneNumber")
    if not raw_number:
        raise HTTPException(status_code=400, detail="Missing phoneNumber in request")
    # Clean formatting
    phone_number = re.sub(r"[^\d+]", "", raw_number)
    if not phone_number.startswith("+"):
        phone_number = f"+34{phone_number}"
    # code might be in different places, but keep original for now
    code = payload["code"]

    call_result = call_client.create_call(
        CallInvite(target=PhoneNumberIdentifier(phone_number)),
        callback_url=ACS_CALLBACK_URL,
        source_caller_id_number=PhoneNumberIdentifier(ACS_SOURCE_PHONE_NUMBER),
        cognitive_services_endpoint=ACS_COGNITIVE_SERVICES_ENDPOINT
    )

    pending_calls[call_result.call_connection_id] = {
        "phone_number": phone_number,
        "code": code
    }

    return {"status": "Voice call initiated"}

@app.post("/events")
async def handle_events(request: Request):
    body = await request.json()
    print("Received ACS event:", body)

    for event in body:
        event_type = event.get("eventType") or event.get("type")
        
        # Handle Event Grid validation event
        if event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
            validation_code = event["data"]["validationCode"]
            print(f"Returning validation code: {validation_code}")
            return {"validationResponse": validation_code}
        
        # Handle communication events
        elif event_type == "Microsoft.Communication.CallConnected":
            call_connection_id = event["data"]["callConnectionId"]
            call_data = pending_calls.get(call_connection_id)

            if call_data:
                code = call_data["code"]
                call_connection = call_client.get_call_connection(call_connection_id)

                text_to_play = f"Hello. Your verification code is {', '.join(code)}."
                # SSML to slow down the speech rate and repeat the message 4 times
                ssml_text = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="-20%">{text_to_play}</prosody><break time="500ms"/>
        <prosody rate="-20%">{text_to_play}</prosody><break time="500ms"/>
        <prosody rate="-20%">{text_to_play}</prosody><break time="500ms"/>
        <prosody rate="-20%">{text_to_play}</prosody>
    </voice>
</speak>"""

                print("TTS SSML to play:", ssml_text)
                ssml_source = SsmlSource(ssml_text=ssml_text)
                call_connection.play_media_to_all(play_source=ssml_source)
                del pending_calls[call_connection_id]
        
        else:
            print(f"Unhandled event type: {event_type}")

    return {"status": "received"}