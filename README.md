# Auth0 MFA SMS/Voice Service

A FastAPI service that provides SMS and voice-based multi-factor authentication (MFA) using Azure Communication Services. This service can be integrated with Auth0 or other authentication providers to send verification codes via SMS or voice calls.

## Features

- 📱 **SMS Verification**: Send verification codes via SMS
- 📞 **Voice Verification**: Send verification codes via automated voice calls
- 🔒 **Webhook Support**: Handle Azure Communication Services events
- ⚡ **FastAPI**: Modern, fast web framework
- 🌐 **Azure Integration**: Powered by Azure Communication Services

## Prerequisites

Before running this project, ensure you have:

1. **Python 3.13+** installed
2. **UV package manager** installed ([Installation guide](https://docs.astral.sh/uv/getting-started/installation/))
3. **Cloudflare account** (for tunnel exposure)
4. **Azure Communication Services** resource with:
   - SMS capability enabled
   - Voice calling capability enabled
   - Phone number acquired
   - Cognitive Services endpoint for Text-to-Speech:
     - Create an AI Foundry resource and deploy Speech.
     - Link the Cognitive Services with your ACS tenant as per the [official documentation](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/azure-communication-services-azure-cognitive-services-integration)

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd auth0-mfa-sms-voice

# Install dependencies using UV
uv sync
```

### 2. Environment Configuration

Copy the example environment file and configure your Azure services:

```bash
cp .env.example .env
```

Edit the `.env` file with your Azure Communication Services configuration:

```env
# Azure Communication Services Configuration
ACS_CONNECTION_STRING="endpoint=https://your-acs-resource.communication.azure.com/;accesskey=your-access-key"

# Callback URL for ACS events (will be your Cloudflare tunnel URL + /events)
ACS_CALLBACK_URL="https://your-tunnel-url.trycloudflare.com/events"

# Source phone number for voice calls (your acquired phone number)
ACS_SOURCE_PHONE_NUMBER="+1234567890"

# Azure Cognitive Services endpoint for TTS
ACS_COGNITIVE_SERVICES_ENDPOINT="https://<your-ai-foundry-tenant-name>.services.ai.azure.com"

# Sender ID for SMS messages
ACS_SENDER_ID="MFA"

# Secret header for authentication
SECRET_HEADER="your-secret-key-here"
```

## Running Locally

### 1. Start the FastAPI Application

```bash
# Activate the UV environment and run the application
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at `http://localhost:8000`

### 2. Expose with Cloudflare Tunnel

Install Cloudflare tunnel (cloudflared) if you haven't already:

```bash
# macOS
brew install cloudflared

# Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

Create a tunnel to expose your local application:

```bash
# Create a tunnel (this will give you a public URL)
cloudflared tunnel --url http://localhost:8000
```

You'll see output like:
```
2024-06-19T10:30:00Z INF Thank you for trying Cloudflare Tunnel. Connectors, if deployed, will not work for this tunnel.
2024-06-19T10:30:00Z INF Your quick Tunnel has been created! Visit it at:
2024-06-19T10:30:00Z INF https://alternate-casio-ted-uri.trycloudflare.com
```

### 3. Update Callback URL

Update your `.env` file with the Cloudflare tunnel URL:

```env
ACS_CALLBACK_URL="https://your-tunnel-url.trycloudflare.com/events"
```

Restart your FastAPI application to pick up the new environment variable.

## Azure Communication Services Setup

### 1. Webhook Registration

Register your webhook endpoint with Azure Communication Services:

1. Go to your ACS resource in the Azure portal
2. Navigate to "Events" 
3. Create a new event subscription
4. Set the endpoint URL to: `https://your-tunnel-url.trycloudflare.com/events`
5. Select the events `Microsoft.Communication.IncomingCall``
6. Save

### 2. Event Grid Validation

When you register the webhook, Azure Event Grid will send a validation event. The application automatically handles this validation process.

## Auth0 Setup

### Note
Currently, this service is configured to support **voice-based MFA** only. SMS-based MFA is not integrated with Auth0 at this time.

### Steps to Configure Auth0 for MFA

1. **Navigate to Multi-factor Authentication**
   - Log in to your Auth0 admin account
   - Go to `Security > Multi-factor Auth`

2. **Configure Phone Provider**
   - Select `Custom` as the provider
   - Choose `Voice` as the method

3. **Add Custom Code**
   - Copy and paste the code under `auth0.js`
   - Add the following dependencies:
     - `uuid` (Version: 11.1.0)
     - `@azure/communication-call-automation` (Version: 1.4.0)

4. **Add Secrets**
   - Add the following secret:
     - `VOICE_API_URL`: Your Cloudflare tunnel URL (e.g., `https://<your-tunnel-subdomain>.trycloudflare.com/send-voice-code`)

5. **Assign Phone Message with Voice**
   - Save the configuration

6. **Test the Setup**
   - Go to `Authentication > Database > Username-Password-Authentication`
   - Test the MFA setup under `Try`.

## API Endpoints

### Send SMS Code
```http
POST /send-text-code
Content-Type: application/json

{
  "data": {
    "messageProfile": {
      "phoneNumber": "+34123456789",
      "msgTemplate": "Your verification code is: 123456"
    }
  }
}
```

### Send Voice Code
```http
POST /send-voice-code
Content-Type: application/json

{
  "phoneNumber": "+34123456789",
  "code": "123456"
}
```

### Webhook Events
```http
POST /events
```
This endpoint receives Azure Communication Services events and Event Grid validation events.

## Development

### Project Structure

```
auth0-mfa-sms-voice/
├── main.py              # FastAPI application
├── pyproject.toml       # Project dependencies
├── requirements.txt     # Generated requirements
├── .env                 # Environment variables (not in git)
├── .env.example        # Environment template
└── README.md           # This file
```

## Deployment

For production deployment, consider:

1. **Environment Variables**: Use proper secret management
2. **HTTPS**: Ensure your webhook endpoint uses HTTPS
3. **Authentication**: Uncomment and configure the authentication headers
4. **Monitoring**: Add proper logging and monitoring
5. **Error Handling**: Enhance error handling for production use

## Troubleshooting

### Common Issues

1. **Webhook Validation Fails**
   - Ensure your tunnel URL is accessible from the internet
   - Check that the `/events` endpoint returns the correct validation response

2. **SMS/Voice Calls Not Working**
   - Verify your ACS connection string is correct
   - Ensure your phone number is properly configured in ACS
   - Check that you have sufficient credits in your Azure account

3. **Environment Variables Not Loading**
   - Ensure `.env` file exists and has correct format
   - Restart the application after changing environment variables

### Logs

Check the application logs for detailed error information:

```bash
# The application logs will show in your terminal where uvicorn is running
# Look for messages like:
# - "Received SMS request body: ..."
# - "Received ACS event: ..."
# - "Returning validation code: ..."
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
