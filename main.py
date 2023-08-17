import discord
import requests

TOKEN = "MTE0MTQ4MjE3OTE5NzY4NTg1MA.GpSpfH.FaPqr88pXlwXeWzVCH9aRd71XwCdwq9pJK6kLs"
API_KEY = ""
MODEL = "gpt-3.5-turbo-16k"
ENDPOINT = "https://free.churchless.tech/v1/chat/completions"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Maintain conversation history
conversations = {}

# Global variable to store last user prompt
last_prompt = {}


def split_long_message(message):
  max_length = 1800
  if len(message) <= max_length:
    return [message]
  split_parts = message.split("\n")
  result_parts = []
  current_part = ""
  for part in split_parts:
    if len(current_part) + len(part) + 1 <= max_length:
      current_part += part + "\n"
    else:
      result_parts.append(current_part)
      current_part = part + "\n"
  result_parts.append(current_part)
  return result_parts


def chatGPT(channel_id, prompt):
  headers = {
      "Authorization": "Bearer " + API_KEY,
      "Content-Type": "application/json"
  }

  conversation = conversations.get(channel_id, [])

  # Use the last user prompt if available
  if channel_id in last_prompt:
    conversation.append({"role": "user", "content": last_prompt[channel_id]})
  else:
    conversation.append({"role": "user", "content": prompt})

  data = {"model": MODEL, "messages": conversation, "max_tokens": 16384}

  try:
    response = requests.post(ENDPOINT, headers=headers, json=data)
    response.raise_for_status()

    return extractMessageFromJSONResponse(response.json())

  except requests.exceptions.RequestException as e:
    conversation.pop()  # Remove the user's message
    raise RuntimeError(e)


def extractMessageFromJSONResponse(response):
  content = response["choices"][0]["message"]["content"]
  return content


def resetConversation(channel_id):
  if channel_id in conversations:
    del conversations[channel_id]


@client.event
async def on_ready():
  print(f'Logged in as {client.user.name}')


@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith('!chat'):
    channel_id = message.channel.id
    prompt = message.content[6:]  # Remove the '!chat ' prefix
    response = chatGPT(channel_id, prompt)

    # Update conversation history
    conversations[channel_id] = conversations.get(channel_id,
                                                  []) + [{
                                                      "role": "user",
                                                      "content": prompt
                                                  }, {
                                                      "role": "assistant",
                                                      "content": response
                                                  }]

    # Split and send long responses
    response_parts = split_long_message(response)
    for part in response_parts:
      await message.channel.send(part)

    # Store the user prompt for potential error recovery
    last_prompt[channel_id] = prompt

  elif message.content.startswith('!forget'):
    channel_id = message.channel.id
    resetConversation(channel_id)
    # Remove stored user prompt when forgetting conversation history
    if channel_id in last_prompt:
      del last_prompt[channel_id]
    await message.channel.send("Conversation history has been forgotten.")


client.run(TOKEN)
