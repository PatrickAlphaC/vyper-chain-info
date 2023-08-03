import logging as log
import os
import time
from pathlib import Path
from typing import List

import requests
from web3 import Web3

log.basicConfig(level=log.INFO)

BASE_EXPLORER_URL = "api?module=contract&action=getsourcecode&address="
EXPLORER_URL_POSTFIX = "&apikey="
ARB_RPC_URL = os.getenv("ARB_RPC_URL")
AVA_RPC_URL = os.getenv("AVA_RPC_URL")
BNB_RPC_URL = os.getenv("BNB_RPC_URL")
ETH_RPC_URL = os.getenv("ETH_RPC_URL")
FANTOM_RPC_URL = os.getenv("FANTOM_RPC_URL")
OPT_RPC_URL = os.getenv("OPT_RPC_URL")
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL")

CHAIN_TO_RPC_URL = {
    "arb": ARB_RPC_URL,
    "ava": AVA_RPC_URL,
    "bnb": BNB_RPC_URL,
    "eth": ETH_RPC_URL,
    "fantom": FANTOM_RPC_URL,
    "opt": OPT_RPC_URL,
    "polygon": POLYGON_RPC_URL,
}

CHAIN_TO_EXPLORER_URL = {
    "arb": "https://api.arbiscan.io/" + BASE_EXPLORER_URL,
    "ava": "https://api.snowtrace.io/" + BASE_EXPLORER_URL,
    "bnb": "https://api.bscscan.com/" + BASE_EXPLORER_URL,
    "eth": "https://api.etherscan.io/" + BASE_EXPLORER_URL,
    "fantom": "https://api.ftmscan.com/" + BASE_EXPLORER_URL,
    "opt": "https://api-optimistic.etherscan.io/" + BASE_EXPLORER_URL,
    "polygon": "https://api.polygonscan.com/" + BASE_EXPLORER_URL,
}

CHAIN_TO_SCANNER_API_KEY = {
    "arb": os.getenv("ARBITRUMSCAN_API_KEY"),
    "ava": os.getenv("SNOWTRACE_API_KEY"),
    "bnb": os.getenv("BSCSCAN_API_KEY"),
    "eth": os.getenv("ETHERSCAN_API_KEY"),
    "fantom": os.getenv("FTMSCAN_API_KEY"),
    "opt": os.getenv("OPTIMISTIC_ETHERSCAN_API_KEY"),
    "polygon": os.getenv("POLYGONSCAN_API_KEY"),
}

POSSIBLE_VYPER_CONTRACTS_DIR = "./possible_vyper_contracts"
VERIFIED_VYPER_CONTRACTS_FILE = "./verified_vyper_contracts.csv"


def main():
    # log.info(f"Getting list of addresses for chain: {CHAIN}")
    vyper_possible_version_folders = get_directory_top_level_content(
        POSSIBLE_VYPER_CONTRACTS_DIR
    )
    for vyper_version_folder in vyper_possible_version_folders:
        log.info(
            f"Getting verified vyper contracts for version: {vyper_version_folder}"
        )
        csv_files_by_chain = get_directory_top_level_content(
            POSSIBLE_VYPER_CONTRACTS_DIR + "/" + vyper_version_folder
        )
        for csv_chain_file in csv_files_by_chain:
            chain = csv_chain_file[: csv_chain_file.find(".csv")]
            log.info(f"Getting verified vyper contracts for chain: {chain}")

            verified_vyper_contracts_with_version = (
                get_verified_vyper_contracts_and_versions_from_csv_path(
                    f"{POSSIBLE_VYPER_CONTRACTS_DIR}/{vyper_version_folder}/",
                    csv_chain_file,
                    chain,
                )
            )

            log.info(f"Getting values for chain: {chain}")
            vyper_contracts_with_values = (
                add_native_balance_from_verified_vyper_addresses_to_dict(
                    chain, verified_vyper_contracts_with_version
                )
            )
            log.info(f"Writing to CSV...")
            write_to_csv(
                vyper_contracts_with_values,
                chain,
            )


def write_to_csv(vyper_contracts_with_values: dict, chain: str):
    """
    Appends items from the dict to the CSV. The dict should be in the following format:
    {
        "chain_name": {
            "address": {
                "version": "0.6.9",
                "native_balance": 420
            }
        }
    }

    Args:
        vyper_contracts_with_values (dict)
        chain (str)
    """
    with open(VERIFIED_VYPER_CONTRACTS_FILE, "a") as file:
        for address, version_and_balance in vyper_contracts_with_values.items():
            version = version_and_balance["version"]
            balance = version_and_balance["native_balance"]
            file.write(f"{chain},{address},{version},{balance}\n")


def add_native_balance_from_verified_vyper_addresses_to_dict(
    chain: str, verified_vyper_contracts_with_version: dict
) -> dict:
    """
    Returns a dict with the key: (address), and values: a dict with keys: "version" and "native_balance". ie:
    {
        "0x1234": {
            "version": "0.6.9",
            "native_balance": 420
        }
    }

    Args:
        chain (str): _description_
        verified_vyper_contracts_with_version (dict): _description_
    """
    for address in verified_vyper_contracts_with_version.keys():
        native_balance = get_native_balance(chain, address)
        verified_vyper_contracts_with_version[address][
            "native_balance"
        ] = native_balance
    return verified_vyper_contracts_with_version


def get_verified_vyper_contracts_and_versions_from_csv_path(
    csv_dir_path: str, csv_file_name: str, chain: str
) -> dict:
    """
    Gets the verified vyper contracts and their versions from a csv file.

    Returns:
        dict with key: address
        and values: vyper_version
    """
    log.info("Loading file from CSV...")
    list_of_addresses: List[str] = read_address_list_from_file(
        csv_dir_path + "/" + csv_file_name
    )

    number_of_addresses = len(list_of_addresses)
    index = 0

    verified_vyper_contracts: dict = {}
    for address in list_of_addresses:
        index = index + 1
        if ((index % 100) == 0) or index == 1:
            log.info(
                f"Getting verified vyper contracts for address {index} of {number_of_addresses}"
            )
        url = build_scanner_url(address, chain)
        response_json = None
        try:
            response_json = requests.get(url).json()
            if "rate limit" in response_json["result"]:
                log.info("Rate limited, sleeping for 6 seconds...")
                time.sleep(6)
                response_json = requests.get(url).json()
        except:
            log.warning(f"Failed to get response from {url}")
        if response_json:
            vyper_version: str = get_vyper_version_from_dict(response_json)
            if vyper_version:
                verified_vyper_contracts[address] = {"version": vyper_version}
    return verified_vyper_contracts


def get_vyper_version_from_dict(response_json: dict) -> str:
    """
    Gets the vyper version from etherscan response

    Returns None if it's not vyper.

    Args:
        response_json (dict): Etherscan API response

    Returns:
        str: Vyper version, or None
    """
    try:
        compiler_version = response_json.get("result", [{}])[0].get(
            "CompilerVersion", None
        )
    except:
        breakpoint()
    if "vyper" in compiler_version:
        return compiler_version[compiler_version.find(":") + 1 :]
    return None


def get_directory_top_level_content(directory: str) -> List[str]:
    dir_path = Path(directory)
    all_items = list(dir_path.glob("*"))
    dir_names = [item.name for item in all_items if item]
    return dir_names


def read_address_list_from_file(csv_chain_file: str):
    with open(csv_chain_file, "r") as file:
        return [line.strip() for line in file.readlines()]


def build_scanner_url(address: str, chain: str):
    explorer_url = CHAIN_TO_EXPLORER_URL[chain]
    api_key = CHAIN_TO_SCANNER_API_KEY[chain]
    return explorer_url + address + EXPLORER_URL_POSTFIX + api_key


# TODO: We could instead get the total estimated TVL of the
def get_native_balance(chain: str, address: str) -> int:
    rpc_url = CHAIN_TO_RPC_URL[chain]
    balance = None
    if rpc_url:
        w3 = Web3(Web3.HTTPProvider(CHAIN_TO_RPC_URL[chain]))
        balance = w3.eth.get_balance(Web3.to_checksum_address(address))
    if not balance:
        log.warning(f"Failed to get balance for address: {address} on chain {chain}")
    return balance


if __name__ == "__main__":
    main()
