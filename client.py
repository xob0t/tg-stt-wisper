import os
import whisper
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError

# Set up your Telegram credentials
API_ID = ''
API_HASH = ''
SESSION_FILE = 'speech_to_text.session'



# Suppress specific warning
# warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Initialize the Whisper model
print("model init")
model = whisper.load_model("base")  # Use "base" or "small" model for faster transcription. Change based on your needs.


# Load session from file if it exists
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            return StringSession(f.read())
    return StringSession()  # Return an empty session if file doesn't exist


# Initialize the Telegram client with StringSession
print("restore sesstion")
client = TelegramClient(load_session(), API_ID, API_HASH)

# Function to transcribe audio files
def transcribe_audio(file_path):
    try:
        result = model.transcribe(file_path)
        return result['text']
    except Exception as e:
        return f"Error transcribing audio: {e}"

# Function to handle Telegram login with password (if needed)
async def login_with_2fa():
    global client
    print("Logging in...")
    phone_number = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()
    try:
        await client.send_code_request(phone_number)
        code = input("Enter the code you received: ")
        await client.sign_in(phone_number, code)  # Pass both phone number and code
        # Save the session string after a successful login
        session_string = client.session.save()
        with open(SESSION_FILE, 'w') as f:
            f.write(session_string)
    except SessionPasswordNeededError:
        password = input("Enter your Telegram password: ")
        await client.sign_in(password=password)
        # Save the session string after a successful login
        session_string = client.session.save()
        with open(SESSION_FILE, 'w') as f:
            f.write(session_string)
        print("Session string saved:", session_string)
    except PhoneNumberInvalidError:
        print("The phone number is invalid. Please make sure it's in the international format, including the country code (e.g., +1234567890).")

# Event listener for incoming voice messages
@client.on(events.NewMessage(incoming=True))
async def handle_incoming_audio(event):
    if event.voice or event.audio:
        # Download the audio file
        file_path = await event.download_media()
        
        # Transcribe the audio
        transcription = transcribe_audio(file_path)

        print("incoming\n", transcription)
        
        # Send the transcription back to the chat
        await event.reply(f"Transcription: {transcription}")

        # Clean up downloaded file
        os.remove(file_path)

# Event listener for outgoing voice messages
@client.on(events.NewMessage(outgoing=True))
async def handle_outgoing_audio(event):
    if event.voice or event.audio:
        # Download the audio file
        file_path = await event.download_media()
        
        # Transcribe the audio
        transcription = transcribe_audio(file_path)


        print("outgoing\n", transcription)
        
        # Send the transcription back to the chat
        await event.respond(f"Transcription: {transcription}")

        # Clean up downloaded file
        os.remove(file_path)

# Run the Telegram client with password support
async def main():
    await client.connect()  # Ensure the client is connected
    if not await client.is_user_authorized():
        await login_with_2fa()  # Handle login process with password (if needed)
    async with client:
        print("Client is running...")
        await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())