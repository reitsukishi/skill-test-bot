import os
import discord
from discord.ext import commands
import random
import json
import asyncio

TOKEN = os.getenv("bot_token")  
LEADERBOARD_FILE = "leaderboard.json"


# File to store quizzes
QUIZ_FILE = "quizzes.json"

QUIZ_ATTEMPTS_FILE = "quiz_attempts.json"

# Load quiz attempts
def load_quiz_attempts():
    try:
        with open(QUIZ_ATTEMPTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save quiz attempts
def save_quiz_attempts(attempts):
    with open(QUIZ_ATTEMPTS_FILE, "w") as f:
        json.dump(attempts, f, indent=4)

quiz_attempts = load_quiz_attempts()


# Load existing leaderboard from file
def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Return empty dict if file doesn't exist

# Save leaderboard to file
def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=4)

# Load quizzes from JSON
def load_quizzes():
    try:
        with open(QUIZ_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Return an empty dictionary if file is missing/corrupt

# Save quizzes to JSON
def save_quizzes():
    with open(QUIZ_FILE, "w") as f:
        json.dump(quizzes, f, indent=4)




# Enable intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Important for reading messages

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# Sample quiz data (Can be expanded)
quizzes = {}

# Load leaderboard at bot start
user_scores = load_leaderboard()

@bot.event
async def on_ready():
    """Load quizzes from file when the bot starts."""
    global quizzes
    quizzes = load_quizzes()
    print(f"✅ Bot is ready! Loaded {len(quizzes)} categories from JSON.")

### 📌 COMMAND: Start Quiz
    @bot.command()
    async def start(ctx, category: str, subcategory: str):
        """Starts a quiz in a given category and subcategory."""
        category = category.lower()
        subcategory = subcategory.lower()

        # Load attempts
        quiz_attempts = load_quiz_attempts()
        user_id = str(ctx.author.id)

        # Check if the user has already attempted this quiz
        if user_id in quiz_attempts and category in quiz_attempts[user_id] and subcategory in quiz_attempts[user_id][category]:
            await ctx.send("❌ You have already attempted this quiz! You cannot take it again.")
            return

        if category not in quizzes or subcategory not in quizzes[category]:
            await ctx.send(
                f"Invalid category or subcategory! Use `!categories` to see available options."
            )
            return

        questions = quizzes[category][subcategory]
        score = 0

        for q in questions:
            if q["type"] == "mcq":
                options_text = "\n".join(
                    [f"{i+1}. {opt}" for i, opt in enumerate(q["options"])])
                await ctx.send(f"**{q['question']}**\n{options_text}")

            elif q["type"] == "one_word":
                await ctx.send(f"**{q['question']}** (One-word answer)")

            elif q["type"] == "true_false":
                await ctx.send(f"**{q['question']}** (True/False)")

            try:
                msg = await bot.wait_for("message",
                                         timeout=15.0,
                                         check=lambda m: m.author == ctx.author)

                if q["type"] == "mcq":
                    selected_option = q["options"][int(msg.content) - 1]
                    if selected_option == q["answer"]:
                        score += 1
                else:
                    if msg.content.lower() == q["answer"].lower():
                        score += 1

            except:
                await ctx.send("⏳ Time's up! Moving to the next question.")

        # Load the existing leaderboard
        leaderboard = load_leaderboard()

        # Update user's score
        username = str(ctx.author)  # Using username instead of ID for readability
        leaderboard[username] = leaderboard.get(username, 0) + score

        # Save updated leaderboard
        save_leaderboard(leaderboard)

        await ctx.send(f"✅ Quiz finished! Your score: {score}")

        # Mark the quiz as attempted for this user
        if user_id not in quiz_attempts:
            quiz_attempts[user_id] = {}
        if category not in quiz_attempts[user_id]:
            quiz_attempts[user_id][category] = {}

        quiz_attempts[user_id][category][subcategory] = True
        save_quiz_attempts(quiz_attempts)

### 📌 COMMAND: Show Available Categories
@bot.command()
async def lists(ctx):
    """Lists all available categories and subcategories."""
    response = "**Available Categories:**\n"
    for cat, subs in quizzes.items():
        response += f"🔹 {cat.capitalize()} → {', '.join(subs.keys())}\n"
    await ctx.send(response)

### 📌 COMMAND: Show Leaderboard
@bot.command()
async def leaderboardx(ctx):
    """displays top ten users with the highest scores"""
    leaderboard = load_leaderboard()

    if not leaderboard:
        await ctx.send("🏆 No scores yet!")
        return

    # Sort users by score in descending order
    sorted_scores = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    leaderboard_text = "\n".join([f"**{i+1}.** **{user}** - {score} points" for i, (user, score) in enumerate(sorted_scores[:10])])
    await ctx.send(f"📊 **Leaderboard:**\n{leaderboard_text}")


### 📌 COMMAND: Show Your Score
@bot.command()
async def myscore(ctx):
    """Shows the user's current score."""
    leaderboard = load_leaderboard()
    username = str(ctx.author)  # Using username instead of ID

    score = leaderboard.get(username, 0)
    await ctx.send(f"🎯 Your total score: {score}")


async def update_score(ctx, score):
    """Updates the leaderboard after a quiz."""
    user_id = str(ctx.author.id)
    leaderboard = load_leaderboard()

    # Update user score
    leaderboard[user_id] = leaderboard.get(user_id, 0) + score
    save_leaderboard(leaderboard)

    await ctx.send(f"✅ Score saved! Your total score is now **{leaderboard[user_id]}**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def createquiz(ctx):
    """Allows an admin to create a new quiz dynamically."""
    await ctx.send("📝 **Let's create a new quiz!** Enter the category name (e.g., Python, JavaScript).")

    try:
        category_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
        category = category_msg.content.lower()

        await ctx.send(f"✅ Category **{category}** set! Now, enter the subcategory name (e.g., Variables, Strings).")

        subcategory_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
        subcategory = subcategory_msg.content.lower()

        if category not in quizzes:
            quizzes[category] = {}
        if subcategory not in quizzes[category]:
            quizzes[category][subcategory] = []

        await ctx.send(f"✅ Subcategory **{subcategory}** set! Now, let's add questions.")

        while True:
            await ctx.send("✍️ Enter the question (or type `done` to finish):")

            question_msg = await bot.wait_for("message", timeout=60.0, check=lambda m: m.author == ctx.author)
            question_text = question_msg.content

            if question_text.lower() == "done":
                break

            await ctx.send("🤖 Select question type: `mcq`, `one_word`, or `true_false`")
            type_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
            question_type = type_msg.content.lower()

            if question_type not in ["mcq", "one_word", "true_false"]:
                await ctx.send("⚠️ Invalid type! Try again.")
                continue

            question_data = {"question": question_text, "type": question_type}

            if question_type == "mcq":
                await ctx.send("🔢 Enter answer choices separated by commas (e.g., Yes, No, Maybe).")
                options_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
                options = options_msg.content.split(",")

                await ctx.send("✅ Now, enter the correct answer:")
                answer_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
                correct_answer = answer_msg.content

                question_data["options"] = [opt.strip() for opt in options]
                question_data["answer"] = correct_answer.strip()

            else:
                await ctx.send("✅ Enter the correct answer:")
                answer_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
                question_data["answer"] = answer_msg.content.strip()

            quizzes[category][subcategory].append(question_data)
            await ctx.send("✅ Question added! Type `done` if you're finished or continue adding more.")

        # Save to JSON file
        save_quizzes()

        await ctx.send(f"🎉 Quiz for `{category} -> {subcategory}` has been saved successfully!")

    except asyncio.TimeoutError:
        await ctx.send("⏳ You took too long to respond. Quiz creation canceled.")

@bot.command()
@commands.has_permissions(administrator=True)
async def deletequiz(ctx):
    """Allows an admin to delete a quiz category or subcategory."""
    await ctx.send("📌 Enter the category name you want to delete (or type `list` to view categories):")

    try:
        category_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
        category = category_msg.content.lower()

        if category == "list":
            categories = list(quizzes.keys())
            if categories:
                await ctx.send(f"📚 Available Categories:\n" + "\n".join(categories))
            else:
                await ctx.send("⚠️ No categories found.")
            return

        if category not in quizzes:
            await ctx.send(f"⚠️ Category `{category}` not found.")
            return

        await ctx.send(f"📌 Enter the subcategory to delete (or type `all` to delete the whole category `{category}`):")
        subcategory_msg = await bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author)
        subcategory = subcategory_msg.content.lower()

        if subcategory == "all":
            await ctx.send(f"⚠️ Are you sure you want to delete the entire category `{category}`? Type `confirm` to proceed.")
            confirm_msg = await bot.wait_for("message", timeout=15.0, check=lambda m: m.author == ctx.author)

            if confirm_msg.content.lower() == "confirm":
                del quizzes[category]
                save_quizzes()
                await ctx.send(f"✅ Category `{category}` and all its quizzes have been deleted!")
            else:
                await ctx.send("❌ Deletion canceled.")
            return

        if subcategory not in quizzes[category]:
            await ctx.send(f"⚠️ Subcategory `{subcategory}` not found in `{category}`.")
            return

        await ctx.send(f"⚠️ Are you sure you want to delete `{category} -> {subcategory}`? Type `confirm` to proceed.")
        confirm_msg = await bot.wait_for("message", timeout=15.0, check=lambda m: m.author == ctx.author)

        if confirm_msg.content.lower() == "confirm":
            del quizzes[category][subcategory]

            # If category is now empty, delete it as well
            if not quizzes[category]:
                del quizzes[category]

            save_quizzes()
            await ctx.send(f"✅ Subcategory `{subcategory}` in `{category}` has been deleted!")
        else:
            await ctx.send("❌ Deletion canceled.")

    except asyncio.TimeoutError:
        await ctx.send("⏳ You took too long to respond. Deletion canceled.")



# Bot login
bot.run(TOKEN)
