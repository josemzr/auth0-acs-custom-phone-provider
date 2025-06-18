exports.onExecuteCustomPhoneProvider = async (event, api) => {
  // 1) get the number and code from Auth0’s payload
  const to = event.notification.recipient;   // "+1-808-555-5555"
  const code = event.notification.code;      // "123456"
  
  // 2) build a payload that your Python endpoint expects
  const payload = { 
    phoneNumber: to,
    code: code
  };

  // 3) call your local Python service
  const res = await fetch(event.secrets.VOICE_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": event.secrets.SECRET_HEADER
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const text = await res.text();
    console.error("Voice API error:", res.status, text);
    throw new Error("Voice call failed");
  }

  console.log(`✅ Voice call triggered for ${to} (code ${code})`);
};