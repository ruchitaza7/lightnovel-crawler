import subprocess
import os
import asyncio
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Dictionary to store tasks by user_id
user_tasks = {}

# Asynchronous function to execute the crawl process and send the file
async def crawl_task(update: Update, url: str) -> None:
    user_id = update.message.from_user.id
    user_folder = f"novels/{user_id}"

    # Create the user-specific folder if it doesn't exist
    os.makedirs(user_folder, exist_ok=True)

    # Base command with placeholders for the user folder
    command = [
        "python",
        "lncrawl",
        "--bot", "console",
        "-s", url,
        "--suppress",
        "--close-directly",
        "--all",
        "--single",
        "-f",
        "--format", "epub",
        "-o", user_folder  # Set the output folder to the user-specific folder
    ]

    try:
        # Run the command in an async thread to avoid blocking the bot
        result = await asyncio.to_thread(subprocess.run, command, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        # Log the result to debug any issues
        print("stdout:", result.stdout.decode())
        print("stderr:", result.stderr.decode())

        # Notify user that crawling is complete
        await update.message.reply_text("The novel has been successfully crawled and saved in EPUB format.")

        # Locate the EPUB file in the user-specific folder
        epub_path = os.path.join(user_folder, "epub")
        if os.path.exists(epub_path):
            # Send the EPUB file to the user
            for file_name in os.listdir(epub_path):
                if file_name.endswith(".epub"):
                    file_path = os.path.join(epub_path, file_name)
                    with open(file_path, 'rb') as file:
                        await update.message.reply_document(file)
                    break
            else:
                await update.message.reply_text("No EPUB file found in the 'epub' folder.")
        else:
            await update.message.reply_text(f"Error: The 'epub' folder for user {user_id} does not exist or is empty.")
        
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"Error: Command failed with return code {e.returncode}")
    except FileNotFoundError:
        await update.message.reply_text("Error: 'lncrawl' is not installed or not found in the system PATH.")
    except asyncio.CancelledError:
        # Handle the task cancellation gracefully
        await update.message.reply_text("The crawling task was cancelled.")
    finally:
        # Clean up any asynchronous tasks if required (e.g., closing resources)
        user_tasks.pop(user_id, None)

# Command handler for '/crawl'
async def crawl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Check if the user already has an active task
    if user_id in user_tasks:
        await update.message.reply_text("You already have a crawl task in progress. Please wait for it to finish or cancel it using /cancel.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a novel URL after the /crawl command.")
        return

    # Extract URL from the user's message
    url = context.args[0]

    # Validate URL format (you could add further validation here)
    if not url.startswith("http"):
        await update.message.reply_text("Invalid URL format. Please provide a valid URL.")
        return

    # Notify user that their request is being processed
    await update.message.reply_text("Processing your request...")

    # Start the task and store it in the user_tasks dictionary
    user_tasks[user_id] = asyncio.create_task(crawl_task(update, url))

# Command handler for '/start'
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to the LNCrawl bot! Send me a novel URL using /crawl <url>.")

# Command handler for '/cancel'
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    
    # Check if the user has an ongoing task
    if user_id in user_tasks:
        # Cancel the ongoing task
        user_tasks[user_id].cancel()
        try:
            # Wait for the task to properly cancel (optional but good practice)
            await user_tasks[user_id]
        except asyncio.CancelledError:
            # Task was cancelled
            await update.message.reply_text("The crawling task has been cancelled.")
        finally:
            # Remove the task from the dictionary only if it exists
            user_tasks.pop(user_id, None)
    else:
        await update.message.reply_text("You don't have any ongoing tasks to cancel.")

def main():
    # Get the bot token from the environment variable
    bot_token = os.getenv('BOT_TOKEN')

    if bot_token is None:
        raise ValueError("Bot token is missing. Please set the BOT_TOKEN environment variable.")

    # Initialize the application with the bot token from the environment variable
    application = Application.builder().token(bot_token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("crawl", crawl))
    application.add_handler(CommandHandler("cancel", cancel))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
