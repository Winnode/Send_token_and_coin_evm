from web3 import Web3
import pandas as pd
import config
import time
from tabulate import tabulate

max_retries = 3

def mulai():
    networks = {
        'ethereum': 'Ethereum',
        'optimism': 'Optimism',
        'bsc': 'Binance Smart Chain (BSC) Testnet',
        'polygon': 'Polygon',
        'polygon_zkevm': 'Polygon ZK-EVM',
        'arbitrum': 'Arbitrum',
        'avalanche': 'Avalanche',
        'fantom': 'Fantom',
        'nova': 'Nova',
        'zksync': 'zkSync',
        'celo': 'Celo',
        'gnosis': 'Gnosis',
        'core': 'Core',
        'harmony': 'Harmony',
        'moonbeam': 'Moonbeam',
        'moonriver': 'Moonriver',
        'linea': 'Linea',
        'base': 'Base'
    }

    print("Pilih jaringan:")
    for i, network in enumerate(networks):
        print(f"{i+1}. {networks[network]}")
    pilihan = int(input("Masukkan pilihan (1-18): "))
    network = list(networks.keys())[pilihan-1]

    rpc_url = config.DATA[network]['rpc']
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token = config.DATA[network]['token']
    chain_id = config.DATA[network]['chain_id']

    print("Pilih jenis transaksi:")
    print("1. Kirim Token")
    print("2. Kirim Coin")
    pilihan = input("Masukkan pilihan (1/2): ")

    if pilihan == "1":
        contract_address = input("Masukkan alamat kontrak: ")

    elif pilihan == "2":
        contract_address = None

    else:
        print("Pilihan tidak valid.")
        return
    contract = None

    if contract_address:
        contract = web3.eth.contract(address=contract_address, abi=config.abi)

    data = pd.read_csv('data.csv')
    jumlah_pengirim = data.shape[0]

    print(web3.is_connected())
    print("===================Mulai Kirim====================")

    if contract:
        print("Nama Token: " + contract.functions.name().call())
    else:
        print("Mengirim Coin")

    successful_transactions = []

    for i in range(jumlah_pengirim):
        retry_count = 0
        alamat_penerima = data.iloc[i]['alamat_penerima']
        private_key = data.iloc[i]['private_key']
        alamat_pengirim = data.iloc[i]['alamat_pengirim']
        send = data.iloc[i]['jumlah_token']

        nonce = web3.eth.get_transaction_count(alamat_pengirim, 'latest')

        if pilihan == "1":
            contract = web3.eth.contract(address=contract_address, abi=config.abi)
            amount = web3.to_wei(str(send), 'ether')
            token_tx = contract.functions.transfer(alamat_penerima, amount).build_transaction({
                'chainId': chain_id,
                'gas': 210000,
                'gasPrice': web3.to_wei('50', 'gwei'),
                'nonce': nonce
            })
            sign_txn = web3.eth.account.sign_transaction(token_tx, private_key=private_key)
        elif pilihan == "2":
            amount = web3.to_wei(str(send), 'ether')
            eth_tx = {
                'to': alamat_penerima,
                'value': amount,
                'gas': 210000,
                'gasPrice': web3.to_wei('50', 'gwei'),
                'nonce': nonce,
                'chainId': chain_id
            }
            sign_txn = web3.eth.account.sign_transaction(eth_tx, private_key=private_key)
        else:
            print("Pilihan tidak valid.")

            return

        try:
            # Send the raw transaction
            web3.eth.send_raw_transaction(sign_txn.rawTransaction)
            if contract:
                successful_transactions.append({
                    'From': alamat_pengirim,
                    'To': alamat_penerima,
                    'Amount': send,
                    'Token': config.DATA[network]['token']
                })
                print(f"Token di Kirim ke Alamat {alamat_penerima} {send}")
            else:
                successful_transactions.append({
                    'From': alamat_pengirim,
                    'To': alamat_penerima,
                    'Amount': send,
                    'Token': config.DATA[network]['token']
                })
                print(f"{token} di Kirim ke Alamat {alamat_penerima} {send}")
        except ValueError as e:
            if "could not replace existing tx" in str(e):
                if retry_count < max_retries:
                    retry_count += 1
                    print("Error: could not replace existing tx. Waiting for confirmation or replacing...")
                    time.sleep(10)
                    continue
                else:
                    print(f"Error: maximum number of retries reached for could not replace existing tx. (Retry {retry_count})")
                    break
            elif "nonce too low" in str(e):
                if retry_count < max_retries:
                    retry_count += 1
                    nonce += 1
                    print(f"Error: nonce too low. Resending with a higher nonce... (Retry {retry_count})")
                else:
                    print(f"Error: maximum number of retries reached for nonce too low. (Retry {retry_count})")
                    break
            else:
                print(f"Error: {e}")
                time.sleep(5)

    # Print the table of successful transactions
        table = []
    for transaction in successful_transactions:
        table.append([
            transaction['From'],
            transaction['To'],
            transaction['Amount'],
            transaction['Token']
        ])

    print(tabulate(table, headers=['From', 'To', 'Amount', 'Chain'], tablefmt='grid'))
		
# Call the function to start sending tokens
mulai()
