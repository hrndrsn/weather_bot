import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Telegram bot token
TOKEN = '7095770713:AAHu02Ru6MGu6qTiddtaQ82ZsnU9LftUdvw'

# ThingSpeak API key and channel ID
THINGSPEAK_API_KEY = 'PA4CZ1GSG29EZE3V'
CHANNEL_ID = '2591669'
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to fetch data from ThingSpeak
def fetch_data_from_thingspeak():
    try:
        url = f'https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={THINGSPEAK_API_KEY}&results=1'
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        logger.info(f"Data fetched: {data}")

        latest_entry = data['feeds'][0]
        return {
            "Humidity": float(latest_entry['field1']) if latest_entry['field1'] is not None else 0.0,
            "AirPressure": float(latest_entry['field2']) if latest_entry['field2'] is not None else 0.0,
            "Temperature": float(latest_entry['field3']) if latest_entry['field3'] is not None else 0.0,
            "Year": int(latest_entry['created_at'][:4]),
            "Month": int(latest_entry['created_at'][5:7]),
            "Day": int(latest_entry['created_at'][8:10]),
            "hour": int(latest_entry['created_at'][11:13])
        }
    except Exception as e:
        logger.error(f"Error fetching data from ThingSpeak: {e}")
        return None

# Function to send POST request
def send_post_request(data):
    try:
        url = "https://iotfastapi-production.up.railway.app/predict/"
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"Response received: {response.json()}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending POST request: {e}")
        return {"error": "Failed to send POST request"}

# Function to format the response message
def format_response(response):
    if "error" in response:
        return "An error occurred: " + response["error"]

    formatted_message = "Prediction Results:\n"
    for prediction in response['predictions']:
        day, humidity, air_pressure, temperature = prediction.split(", ")
        formatted_message += (
            f"{day}\n"
            f"  Predicted Humidity: {humidity.split(': ')[1]}\n"
            f"  Predicted Air Pressure: {air_pressure.split(': ')[1]}\n"
            f"  Predicted Temperature: {temperature.split(': ')[1]}\n"
        )
    return formatted_message

# Command handler for /forecast
async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info("Handling /forecast command...")
        data = fetch_data_from_thingspeak()
        if not data:
            await update.message.reply_text("Failed to fetch data from ThingSpeak.")
            return

        response = send_post_request(data)
        formatted_message = format_response(response)
        await update.message.reply_text(formatted_message)
    except Exception as e:
        logger.error(f"Error in forecast: {e}")
        await update.message.reply_text("An error occurred while processing your request.")

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! Use /forecast to send a request.")

def main():
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("forecast", forecast))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
