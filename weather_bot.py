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
    url = f'https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={THINGSPEAK_API_KEY}&results=1'
    response = requests.get(url)
    data = response.json()

    logger.info(f"Data fetched: {data}")

    # Extract the latest data point
    latest_entry = data['feeds'][0]
    return {
        "Humidity": float(latest_entry['field1']),
        "AirPressure": float(latest_entry['field2']),
        "Temperature": float(latest_entry['field3']),
        "Year": int(latest_entry['created_at'][:4]),
        "Month": int(latest_entry['created_at'][5:7]),
        "Day": int(latest_entry['created_at'][8:10]),
        "hour": int(latest_entry['created_at'][11:13])
    }

# Function to send POST request
def send_post_request(data):
    url = "https://iotfastapi-production.up.railway.app/predict/"
    response = requests.post(url, json=data)
    logger.info(f"Response received: {response.json()}")
    return response.json()

# Function to format the response message
def format_response(response):
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