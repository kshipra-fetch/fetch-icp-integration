# Dummy Bitcoin Integration: ICP + Fetch.ai

This project demonstrates a collaborative integration between Internet Computer Protocol (ICP) and Fetch.ai, showcasing how to build a Bitcoin service using ICP canisters in the backend and Fetch.ai agents which can be queried via the AISI:One LLM. 

## Project Structure

```
dummy-bitcoin/
├── agent.py              # Fetch.ai agent implementation
├── private_keys.json     # Private keys for the agent
└── btc-dummy/           # ICP canister implementation
    └── src/
        └── backend/
            └── index.ts  # Dummy Bitcoin HTTP server
```

## ICP Component

The ICP component (`btc-dummy/src/backend/index.ts`) implements a dummy HTTP server with the following endpoints:

- `/get-balance` - Returns dummy balance for a Bitcoin address
- `/get-utxos` - Returns dummy UTXOs for a Bitcoin address
- `/get-current-fee-percentiles` - Returns dummy fee percentiles
- `/get-p2pkh-address` - Returns a dummy P2PKH address
- `/send` - Simulates sending Bitcoin to an address
- `/dummy-test` - Test endpoint for basic connectivity

Note: This is a dummy implementation that returns mock data. The actual implementation needs to be amended.

## Fetch.ai Component

The Fetch.ai component (`agent.py`) implements an intelligent agent using the Chat Protocol, making it discoverable by ASI:One. The agent:

- Processes natural language queries about Bitcoin operations
- Converts user queries into appropriate API calls to the ICP canister
- Define the ICP endpoints as functions with descriptions and required parameters in the agent.
- Use a LLM to decide which endpoint needs to be called based on user query and the defined functions.
- Handles responses and presents them in a user-friendly format
- Supports various Bitcoin-related queries like checking balances, UTXOs, fees, and sending transactions

### Install uagents
```bash
pip install uagents
```


### Running the Agent

1. Start the agent:
```bash
python3 agent.py
```

2. The agent will start and display its address and inspector URL:

```
INFO: [test-ICP-agent]: Starting agent with address: agent1qdla8t5m3wm7tnua69jjv3p4cr4ugmzmcj95jy9vrh4209scxs02qlxwt0g
INFO: [test-ICP-agent]: Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8001&address=agent1qdla8t5m3wm7tnua69jjv3p4cr4ugmzmcj95jy9vrh4209scxs02qlxwt0g
```

3. Click on the Agent Inspector link to connect the agent with Agentverse via Mailbox
![Mailbox connect](dummy-bitcoin/images/mailbox-connect.png)

![Mailbox options](dummy-bitcoin/images/mailbox-options.png)

![Mailbox done](dummy-bitcoin/images/mailbox-done.png)



4. Test the agent using the Chat interface with queries like:
   - Once connected, click on Agent Profile
   ![Agent Profile](dummy-bitcoin/images/agent-profile.png)

   - Click on `Chat with Agent` to test the flow
    ![Chat with Agent](dummy-bitcoin/images/chat-with-agent.png)

   - Type in yyour queries in the UI
    ![Type Query](dummy-bitcoin/images/chat-ui.png)



## Example Queries

The agent supports various types of queries:

### Balance Queries
- What's the balance of address tb1qexample1234567890?
- Can you check how many bitcoins are in tb1qabcde000001234567?

### UTXO Queries
- What UTXOs are available for address tb1qexampleutxo0001?
- List unspent outputs for tb1qunspentoutputs111

### Fee Queries
- What are the current Bitcoin fee percentiles?
- Show me the latest fee percentile distribution

### Transaction Queries
- Send 10,000 satoshis to tb1qreceiver000111
- Transfer 50000 sats to tb1qsimplewalletabc

