from rich.console import Console
from rich import print
import os
import time
import inquirer
from dotenv import load_dotenv
from atproto import Client, models
import google.generativeai as genai
import random
from requests.exceptions import HTTPError
import praw
import wikipedia
from newsapi import NewsApiClient
import re
from fuzzywuzzy import fuzz

# ------------------------------------------------------------
# Load environment variables
load_dotenv()

LEFT_USER = os.getenv('LEFT_USER')
LEFT_PASS = os.getenv('LEFT_PASS')
RIGHT_USER = os.getenv('RIGHT_USER')
RIGHT_PASS = os.getenv('RIGHT_PASS')

GOOGLE_API_KEY = os.getenv('Google')
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
REDDIT_USER_AGENT_user = os.getenv('REDDIT_USER_AGENT_user')
REDDIT_USER_AGENT_pass = os.getenv('REDDIT_USER_AGENT_pass')

genai.configure(api_key=GOOGLE_API_KEY)

# We will assume these models are accessible via genai.
final_model = genai.GenerativeModel("gemini-1.5-pro")
small_model = genai.GenerativeModel("gemini-1.5-flash")
mid_model = genai.GenerativeModel("gemini-1.0-pro")

console = Console()

import os

# Define the root file path
root_file_path = r"C:\Users\icuul\Desktop\CODE\Projects\LLMTHEISM\Politician_bot\Prompts"

# Define file paths relative to the root
file_paths = {
    "persona_and_task_left": os.path.join(root_file_path, "persona_and_task_left.txt"),
    "persona_and_task_right": os.path.join(root_file_path, "persona_and_task_right.txt"),
    "persona_and_task_select_reply_left": os.path.join(root_file_path, "persona_and_task_select_reply_left.txt"),
    "persona_and_task_select_reply_right": os.path.join(root_file_path, "persona_and_task_select_reply_right.txt"),
    "persona_and_task_reply_left": os.path.join(root_file_path, "persona_and_task_reply_left.txt"),
    "persona_and_task_reply_right": os.path.join(root_file_path, "persona_and_task_reply_right.txt"),
    "Meprompt": os.path.join(root_file_path, "Meprompt.txt")
}

# Dictionary to store file content
file_contents = {
    key: open(path, 'r', encoding='utf-8').read() if os.path.exists(path) 
    else f"No information found for {os.path.basename(path)}."
    for key, path in file_paths.items()
}

# Assign to variables for easier access
persona_and_task_left = file_contents["persona_and_task_left"]
persona_and_task_right = file_contents["persona_and_task_right"]
persona_and_task_select_reply_left = file_contents["persona_and_task_select_reply_left"]
persona_and_task_select_reply_right = file_contents["persona_and_task_select_reply_right"]
persona_and_task_reply_left = file_contents["persona_and_task_reply_left"]
persona_and_task_reply_right = file_contents["persona_and_task_reply_right"]
meprompt = file_contents["Meprompt"]


def get_additional_info(query, num_results=7, max_retries=3, delay=5, account_choice="left"):
    from brave import Brave
    import time
    console.print(f"\n[bold bright_yellow][Step] Fetching additional info for query: {query}...[/bold bright_yellow]")
    brave = Brave(api_key=BRAVE_API_KEY)

    # Dynamically set the goggles URL based on account choice
    if account_choice == "left":
        goggle_url = "https://raw.githubusercontent.com/allsides-news/brave-goggles/main/left.goggles"
    else:
        goggle_url = "https://raw.githubusercontent.com/allsides-news/brave-goggles/main/right.goggles"

    retries = 0
    while retries < max_retries:
        try:
            search_results = brave.search(q=query, goggles_id=goggle_url, count=num_results, result_filter="web,news")
            web_results = [
                {"title": result.get("title"), "description": result.get("description")}
                for result in getattr(search_results, 'web_results', [])
            ]
            news_results = [
                {"title": result.get("title"), "description": result.get("description")}
                for result in getattr(search_results, 'news_results', [])
            ]
            additional_info = web_results + news_results
            console.print(f"[bold bright_cyan]Additional Info for '{query}': {additional_info}[/bold bright_cyan]")
            return additional_info
        except HTTPError as e:
            if e.response.status_code == 429:
                console.print(f"[bold orange4]Rate limit hit. Retrying in {delay} seconds...[/bold orange4]")
                time.sleep(delay)
                retries += 1
            else:
                raise
    console.print("[bold red3]Max retries reached. Returning empty results.[/bold red3]")
    return []


def get_reddit_discussion(topic, limit=1):
    console.print(f"\n[bold bright_magenta][Step] Fetching Reddit discussions for topic: {topic}...[/bold bright_magenta]")
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                         client_secret=REDDIT_CLIENT_SECRET,
                         user_agent=REDDIT_USER_AGENT,
                         username=REDDIT_USER_AGENT_user,
                         password=REDDIT_USER_AGENT_pass,
                         check_for_async=False)
    discussions = []
    subreddit = reddit.subreddit("all")
    for submission in subreddit.search(topic, sort='top', time_filter='week', limit=limit):
        comments = [comment.body for comment in submission.comments[:7] if isinstance(comment, praw.models.Comment)]
        discussions.append({
            'title': submission.title,
            'comments': comments
        })
    console.print(f"[bold bright_yellow]Reddit Discussions for '{topic}': {discussions}[/bold bright_yellow]")
    return discussions


def get_news_data():
    console.print("\n[bold bright_cyan][Step] Fetching News data...[/bold bright_cyan]")
    file_path = r'C:\Users\icuul\Desktop\CODE\Projects\LLMTHEISM\Politician_bot\source_ids.txt'
    try:
        with open(file_path, 'r') as file:
            file_contents = file.read()
            sources = file_contents.replace('\n', ' ').split()
            console.print(f"[bold orange4]News Sources: {sources}[/bold orange4]")
    except FileNotFoundError:
        console.print(f"[bold red3]Error: File not found at {file_path}[/bold red3]")
        sources = []

    newsapi = NewsApiClient(api_key=os.getenv('News_api'))
    sources_string = ",".join(sources) if sources else "bbc-news"
    top_headlines = newsapi.get_top_headlines(
        sources=sources_string,
        language='en',
    )
    filtered_news = [
        {
            'source': article['source']['name'],
            'title': article['title'],
            'description': article['description'],
            'content': article['content']
        }
        for article in top_headlines.get('articles', [])
    ]
    console.print(f"[bold bright_green]News Data: {filtered_news}[/bold bright_green]")
    return filtered_news


def get_wikipedia_data(keywords):
    console.print("\n[bold bright_magenta][Step] Fetching Wikipedia data...[/bold bright_magenta]")
    wikipedia_data = []
    for keyword in keywords:
        try:
            summary = wikipedia.summary(keyword, sentences=3)
            wikipedia_data.append({'keyword': keyword, 'summary': summary})
            console.print(f"[bold bright_yellow]Wikipedia Data for '{keyword}': {summary}[/bold bright_yellow]")
        except Exception as e:
            console.print(f"[bold red3]Error fetching Wikipedia data for {keyword}: {e}[/bold red3]")
    return wikipedia_data

additional_instructions = meprompt

def generate_content(persona_and_task, final_context, news_data, brave_data, additional_instructions, wiki_data=None, reddit_data=None):
    console.print("\n[bold cyan][Step] Generating final content...[/bold cyan]")
    wiki_data = wiki_data if wiki_data else []
    reddit_data = reddit_data if reddit_data else []
    prompt = f"""
##Original Bigger Picture (News):
{news_data}

##Biased News (Brave + Google):
{brave_data}

##Persona and Task Information:
{persona_and_task}

##Additional Instructions:
{additional_instructions}

##Contextual Info (if any):
Wikipedia: {wiki_data}
Reddit: {reddit_data}

##Thread Context (if any):
{final_context}
"""
    response = final_model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=4000,
            temperature=1.8,
        ),
    )
    tweet = response.text.strip()
    console.print(f"[bold bright_yellow]Generated Content: {tweet}[/bold bright_yellow]")
    return tweet


instruction = ''' Jailbrake placeholder'''
instruction2 = '''Jailbrake placeholder'''


def extract_keywords_small_model(text, num_keywords=7):
    console.print("\n[bold bright_magenta]Extracting Keywords with Small Model...[/bold bright_magenta]")
    prompt = f"Extract {num_keywords} keywords from the following text:\n{text}\nOUTPUT RULE: only keywords separated with commas that can deepen the research about the text"
    response = small_model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=200,
            temperature=0.7,
        ),
    )
    keywords = [kw.strip() for kw in response.text.split(',') if kw.strip()]
    keywords = keywords[:num_keywords]
    console.print(f"[bold bright_cyan]Extracted Keywords: {keywords}[/bold bright_cyan]")
    return keywords


def select_comment_mid_model(thread_context, account_choice="left"):
    console.print("\n[bold bright_magenta]Selecting comment to reply to (Mid Model)...[/bold bright_magenta]")
    # Not used in the new workflow, but leaving here.
    persona_and_task_select_reply = persona_and_task_select_reply_left if account_choice == "left" else persona_and_task_select_reply_right

    prompt = f"""
{persona_and_task_select_reply}

Select the most relevant comment to reply to from the following thread:
{thread_context}

##OUTPUT RULE: only output the comment to reply to verbatim and nothing else
"""
    response = mid_model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=1000,
            temperature=0.7,
        ),
    )
    selected_comment = response.text.strip()
    console.print(f"[bold bright_green]Selected Comment: {selected_comment}[/bold bright_green]")
    return selected_comment


def select_thread_mid_model(timeline_posts, account_choice="left"):
    console.print("\n[bold bright_magenta]Selecting thread to reply to (Mid Model)...[/bold bright_magenta]")
    # Not used in the new workflow, but leaving here.
    persona_and_task_select_reply = persona_and_task_select_reply_left if account_choice == "left" else persona_and_task_select_reply_right

    timeline_text = "\n".join([f"{idx}: {p.post.author.display_name}: {p.post.record.text}" 
                               for idx, p in enumerate(timeline_posts)])
    prompt = f"""
{persona_and_task_select_reply}

Select the most relevant post (by index) from the following timeline to start a thread for reply:
{timeline_text}
"""
    response = mid_model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=500,
            temperature=0.7,
        ),
    )
    selected_idx_str = response.text.strip()

    match = re.search(r'\b\d+\b', selected_idx_str)
    if match:
        selected_idx = int(match.group(0))
    else:
        selected_idx = 0  # Default to 0 if no integer is found

    console.print(f"[bold bright_green]Selected Thread Index: {selected_idx}[/bold bright_green]")
    return selected_idx


def find_best_match(selected_text, posts_in_thread):
    best_match = None
    highest_similarity = 0
    for p in posts_in_thread:
        if hasattr(p, 'post'):
            comment_text = p.post.record.text
            similarity = fuzz.ratio(selected_text.strip().lower(), comment_text.strip().lower())
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = p
    return best_match if highest_similarity > 75 else None


def get_timeline(client):
    timeline = client.get_timeline(algorithm='reverse-chronological')
    posts = []
    console.print('\n[bold bright_cyan]Home (Following):[/bold bright_cyan]\n')
    for idx, feed_view in enumerate(timeline.feed):
        action = 'New Post'
        if feed_view.reason:
            action_by = feed_view.reason.by.handle
            action = f'Reposted by @{action_by}'

        post = feed_view.post.record
        author = feed_view.post.author
        console.print(f"[{idx}] [{action}] {author.display_name}: {post.text}")
        posts.append(feed_view)
    return posts

def get_thread(client, post_uri):
    res = client.get_post_thread(uri=post_uri, depth=99, parent_height=99)
    thread = res.thread
    return thread

def display_thread(thread):
    console.print('\n[bold bright_magenta]Thread View:[/bold bright_magenta]\n')
    posts_in_thread = []

    def traverse_thread(thread_post, level=0):
        if isinstance(thread_post, models.AppBskyFeedDefs.ThreadViewPost):
            prefix = "  " * level
            console.print(f"{prefix}[{len(posts_in_thread)}] {thread_post.post.author.display_name}: {thread_post.post.record.text}")
            posts_in_thread.append(thread_post)

        if thread_post.parent and isinstance(thread_post.parent, models.AppBskyFeedDefs.ThreadViewPost):
            traverse_thread(thread_post.parent, level - 1)

        if hasattr(thread_post, 'replies') and thread_post.replies:
            for reply in thread_post.replies:
                traverse_thread(reply, level + 1)

    traverse_thread(thread)
    return posts_in_thread

def tweet_generation_workflow(account_choice="left"):
    # Set persona_and_task based on account_choice
    persona_and_task = persona_and_task_left if account_choice == "left" else persona_and_task_right

    # 1. Get news data
    news_data = get_news_data()

    # 2. Extract keywords
    news_text = " ".join([n['title'] + " " + (n['description'] or '') for n in news_data])
    keywords = extract_keywords_small_model(news_text, 10)

    # 3. Get additional context from Brave
    brave_data = []
    for kw in keywords:
        brave_data.extend(get_additional_info(kw, account_choice=account_choice))
        time.sleep(1)

    # 4. Generate final tweet
    final_tweet = generate_content(persona_and_task, "", news_data, brave_data, "Generate a final tweet of less than 300 characters. Use only lowercase and never use hashtags, keep it condensed")
    return final_tweet[:300]

def post_tweet(client, text, parent_ref=None, root_ref=None):
    if parent_ref and root_ref:
        return client.send_post(
            text=text,
            reply_to=models.AppBskyFeedPost.ReplyRef(parent=parent_ref, root=root_ref)
        )
    else:
        return client.send_post(text=text)

def get_persona_and_task(account_choice):
    if account_choice == "left":
        return persona_and_task_left
    else:
        return persona_and_task_right

def conversation_flow(start_side="left"):
    # Determine accounts
    if start_side == "left":
        start_user = LEFT_USER
        start_pass = LEFT_PASS
        other_side = "right"
    else:
        start_user = RIGHT_USER
        start_pass = RIGHT_PASS
        other_side = "left"

    # Log in start side
    start_client = Client()
    start_client.login(start_user, start_pass)

    # Log in other side
    if other_side == "left":
        other_user = LEFT_USER
        other_pass = LEFT_PASS
    else:
        other_user = RIGHT_USER
        other_pass = RIGHT_PASS

    other_client = Client()
    other_client.login(other_user, other_pass)

    # Step 1: Generate initial tweet from start_side
    initial_tweet_text = tweet_generation_workflow(account_choice=start_side)
    initial_post = post_tweet(start_client, initial_tweet_text) 
    root_uri = initial_post.uri

    console.print(f"[bold green]Initial tweet posted by {start_side}: {initial_tweet_text}[/bold green]\n")

    # We want a total of 10 replies (5 by each side)
    # We'll alternate sides. The order after initial tweet:
    # round 1 reply: other_side
    # round 2 reply: start_side
    # and so forth...
    #
    # Each time we generate a reply, we fetch the full thread, feed it as context.
    # We'll always reply to the last message in the thread.

    current_side = other_side
    parent_uri = root_uri
    number_of_replies = 10

    for i in range(number_of_replies):
        # Get current client's persona and data
        if current_side == "left":
            current_client = other_client if other_side == "left" else start_client if start_side == "left" else None
        else:
            current_client = other_client if other_side == "right" else start_client if start_side == "right" else None

        # Retrieve the full thread
        thread = get_thread(current_client, root_uri)
        posts_in_thread = display_thread(thread)

        # Prepare context: all previous posts
        thread_context = "\n\n".join([p.post.record.text for p in posts_in_thread if hasattr(p, 'post')])

        # Now generate a reply from current_side
        persona_and_task = get_persona_and_task(current_side)

        # Extract some keywords from the entire thread to get more context
        # (Optional step, just to add complexity)
        combined_thread_text = " ".join([p.post.record.text for p in posts_in_thread])
        comment_keywords = extract_keywords_small_model(combined_thread_text, 5)
        wiki_data = get_wikipedia_data(comment_keywords)
        reddit_data = []
        for kw in comment_keywords:
            reddit_data.extend(get_reddit_discussion(kw))
        additional_brave_data = []
        for kw in comment_keywords:
            additional_brave_data.extend(get_additional_info(kw, account_choice=current_side))
            time.sleep(1)

        instructions_for_tone = "Reply directly to the last post in the thread. Continue the conversation. Use only lowercase and never use hashtags, keep it condensed - less than 300 characters."

        # The last post in the thread will be the parent for the reply
        last_post = posts_in_thread[-1]
        parent_ref = models.create_strong_ref(last_post.post)
        root_ref = models.create_strong_ref(posts_in_thread[0].post)  # root is always the first

        # Generate the reply text
        reply_text = generate_content(
            persona_and_task,
            thread_context,
            [],
            additional_brave_data,
            instructions_for_tone,
            wiki_data=wiki_data,
            reddit_data=reddit_data
        )

        # Post the reply
        reply_post = post_tweet(current_client, reply_text[:300], parent_ref=parent_ref, root_ref=root_ref)
        console.print(f"[bold cyan]{current_side} replied with: {reply_text[:300]}[/bold cyan]\n")

        # Switch sides
        current_side = other_side if current_side == start_side else start_side

    console.print("[bold bright_magenta]Conversation completed with 10 replies![/bold bright_magenta]")

def main():
    # Ask user for starting side
    questions = [
        inquirer.List('start_side',
                      message="Who starts the thread?",
                      choices=['left', 'right']
                      ),
    ]
    answers = inquirer.prompt(questions)
    start_side = answers['start_side']
    conversation_flow(start_side=start_side)


if __name__ == '__main__':
    main()
