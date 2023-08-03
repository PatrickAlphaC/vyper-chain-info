# Vyper Chain Info

A repo to collect data on existing vyper contracts in the ecosystem. 

This is meant to be a "sort-of quick" project so it's not perfect.

This README.md is pretty bad too. 

# Strategy

We took the strategy:

1. Run a dune analytics query for the following chains, to get any contract that had similar bytecode to a vyper contract:
- Avalanche
- Arbitrum
- BNB
- Ethereum
- Fantom
- Optimism
- Polygon

The results from those queries are in the `possible_vyper_contracts`. They can be considered a superset of all Vyper contracts on those chains for the following vyper versions:

```
0.2.11-0.3.9
```

With some versions `0.2.0` - `0.2.8` in there. 

2. Took those addresses, and ran them through a script that checked them against etherscan, or etherscan-like block explorer to see if they are verified etherscan. 

If they were verified, we placed them into `verified_vyper_contracts.csv`, along with their:
- chain
- address
- native balance
- vyper version

This is considered a subset as non-verified contracts get filtered out. 

# Getting started

You'll need environment variables for Etherscan and Etherscan-like explorers and RPC URLs for each chain. See the python code for more details. 

After cloning the repo, run:

```
poetry install
poetry run python3 confirm_vyper_contracts_and_value.py
```

To get the output again. 

# Queries
- For avalanche, you need to use `avalanche_c.creation_traces`

# Resources used
- [How to get Vyper versions from bytecode post 0.3.4](https://github.com/vyperlang/vyper/pull/2860#issuecomment-1279717236)
- [How to check if a contract might be vyper prior to 0.3.3](https://github.com/banteg/erigon-kv/blob/17f66e2ce0cf0cb269b298a6d805fae50cb7c003/examples/compilers.py#L18-L19)

# Not 100% sure
- Do Dune analytics `creation_traces` include transactions created by other contracts?
  - [Asked here](https://ethereum.stackexchange.com/questions/153021/do-dune-analytics-creation-traces-data-include-contracts-created-by-other-cont)


# Results

The results of this are in `verified_vyper_contracts.csv` which has the following:

1. The Chain
2. The Contract Address
3. The vyper version
4. The native balance of the contract
   1. If the script had an issue, it's just `NONE`

