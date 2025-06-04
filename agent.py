import requests
import openai
import json
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
)
from uagents import Agent, Context, Protocol
from datetime import datetime, timezone, timedelta
from uuid import uuid4





openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your key

CANISTER_ID = "bkyz2-fmaaa-aaaaa-qaaaq-cai"
BASE_URL = "http://127.0.0.1:4943"

HEADERS = {
    "Host": f"{CANISTER_ID}.localhost",
    "Content-Type": "application/json"
}

# Function definitions for OpenAI function calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_fee_percentiles",
            "description": "Gets the 100 fee percentiles measured in millisatoshi/byte.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Returns the balance of a given Bitcoin address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "The Bitcoin address to check."
                    }
                },
                "required": ["address"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_utxos",
            "description": "Returns the UTXOs of a given Bitcoin address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "The Bitcoin address to fetch UTXOs for."
                    }
                },
                "required": ["address"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send",
            "description": "Sends satoshis from this canister to a specified address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {
                        "type": "string",
                        "description": "The destination Bitcoin address."
                    },
                    "amountInSatoshi": {
                        "type": "number",
                        "description": "Amount to send in satoshis."
                    }
                },
                "required": ["destinationAddress", "amountInSatoshi"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

async def call_icp_endpoint(func_name: str, args: dict):
    if func_name == "get_current_fee_percentiles":
        url = f"{BASE_URL}/get-current-fee-percentiles"
        response = requests.post(url, headers=HEADERS, json={})
    elif func_name == "get_balance":
        url = f"{BASE_URL}/get-balance"
        response = requests.post(url, headers=HEADERS, json={"address": args["address"]})
    elif func_name == "get_utxos":
        url = f"{BASE_URL}/get-utxos"
        response = requests.post(url, headers=HEADERS, json={"address": args["address"]})
    elif func_name == "send":
        url = f"{BASE_URL}/send"
        response = requests.post(url, headers=HEADERS, json=args)
    else:
        raise ValueError(f"Unsupported function call: {func_name}")
    
    response.raise_for_status()
    return response.json()

async def process_query(query: str, ctx: Context) -> str:
    try:
        # First test the dummy endpoint
        try:
            ctx.logger.info("Testing dummy endpoint...")
            dummy_result = await call_icp_endpoint("get_current_fee_percentiles", {})
            ctx.logger.info(f"Dummy endpoint response: {dummy_result}")
        except requests.exceptions.RequestException as e:
            ctx.logger.error(f"Failed to connect to the canister: {e}")
            return "Failed to connect to the Bitcoin canister. Please try again later."

        # Send to OpenAI for function call extraction
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto"
        )

        # Extract function calls from response
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return "I couldn't determine what Bitcoin information you're looking for. Please try rephrasing your question."

        # Process each function call
        results = []
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            ctx.logger.info(f"Executing {func_name} with arguments: {arguments}")
            
            try:
                result = await call_icp_endpoint(func_name, arguments)
                results.append(f"{func_name} result: {json.dumps(result, indent=2)}")
            except requests.exceptions.RequestException as e:
                results.append(f"Error executing {func_name}: {str(e)}")

        return "\n".join(results)

    except Exception as e:
        ctx.logger.error(f"Error processing query: {str(e)}")
        return f"An error occurred while processing your request: {str(e)}"

agent = Agent(
    name='test-ICP-agent',
    port=8001,
    mailbox=True
)
chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(model=ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    try:
        ack = ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id
        )
        await ctx.send(sender, ack)

        for item in msg.content:
            if isinstance(item, StartSessionContent):
                ctx.logger.info(f"Got a start session message from {sender}")
                continue
            elif isinstance(item, TextContent):
                ctx.logger.info(f"Got a message from {sender}: {item.text}")
                response_text = await process_query(item.text, ctx)
                ctx.logger.info(f"Response text: {response_text}")
                response = ChatMessage(
                    timestamp=datetime.now(timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=response_text)]
                )
                await ctx.send(sender, response)
            else:
                ctx.logger.info(f"Got unexpected content from {sender}")
    except Exception as e:
        ctx.logger.error(f"Error handling chat message: {str(e)}")
        error_response = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"An error occurred: {str(e)}")]
        )
        await ctx.send(sender, error_response)

@chat_proto.on_message(model=ChatAcknowledgement)
async def handle_chat_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")
    if msg.metadata:
        ctx.logger.info(f"Metadata: {msg.metadata}")

agent.include(chat_proto)

if __name__ == "__main__":
    agent.run()


"""
Queries for /get-balance
What's the balance of address tb1qexample1234567890?

Can you check how many bitcoins are in tb1qabcde000001234567?

Show me the balance of this Bitcoin wallet: tb1qtestwalletxyz.

🧾 Queries for /get-utxos
What UTXOs are available for address tb1qexampleutxo0001?

List unspent outputs for tb1qunspentoutputs111.

Do I have any unspent transactions for tb1qutxotest9999?

🧾 Queries for /get-current-fee-percentiles
What are the current Bitcoin fee percentiles?

Show me the latest fee percentile distribution.

How much are the Bitcoin network fees right now?

🧾 Queries for /get-p2pkh-address
What is my canister’s P2PKH address?

Generate a Bitcoin address for me.

Give me a Bitcoin address I can use to receive coins.

🧾 Queries for /send
Send 10,000 satoshis to tb1qreceiver000111.

Transfer 50000 sats to tb1qsimplewalletabc.

I want to send 120000 satoshis to tb1qdonationaddress001.

🧾 General/Dummy Test
Run the dummy test endpoint.

Can I see a test response?

Hit the dummy-test route to make sure it works.
"""