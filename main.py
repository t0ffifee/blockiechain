import requests
import json
from flask import Flask, jsonify, request
from werkzeug.wrappers import response

import blockchain
import transaction
import transaction_pool
import wallet

"""
main.py
 - webserver die reageert op commands
 - gemaakt met flask

commands:
 - mine
 - show chain
 - show last block
 - show address, balance
 - create transaction
"""

app = Flask(__name__)
node_name = 'bobby'
node_identifier = node_name

def to_dict(obj):
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': to_dict(block_chain.chain), 
        'length': len(block_chain.chain),
    }
    return response, 200

@app.route('/address', methods=['GET'])
def get_address():
    response = {
        'address': node_address
    }
    return response, 200

@app.route('/balance', methods=['GET'])
def get_balance():
    amount = wallet.get_balance(node_address, unspent_txouts)
    response = {
        'amount': amount
    }
    return response, 200

@app.route('/lastblock', methods=['GET'])
def last_block():
    response = {
        'block': to_dict(block_chain.last_block)
    }
    return response, 200

@app.route('/unspentTransactions', methods=['GET'])
def unspent_transactions():
    response = {
        'utxos': to_dict(unspent_txouts)
    }
    return response, 200

@app.route('/myUnspentTransactions', methods=['GET'])
def my_unspent_transactions():
    response = {
        'utxos': to_dict(wallet.find_unspent_txouts(node_address, unspent_txouts)),
        'address': node_address
    }
    return response, 200

@app.route('/transactionpool', methods=['GET'])
def get_transactionpool():
    response = {
        'transaction pool': to_dict(tx_pool.transaction_pool)
    }
    return response, 200

@app.route('/mine', methods=['POST'])
def mine_block():
    coinbase = transaction.get_coinbase_transaction(node_address, len(block_chain.chain))
    transactions = [coinbase]
    transactions += tx_pool
    block = block_chain.generate_new_block(transactions)
    block_chain.chain.append(block)

    response = {
        'new block': to_dict(block)
    }
    return response, 200

@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    
    required = ['recipient', 'amount']
    if not all(k in values for k in required):
        return 'missing values', 400
    
    tx = wallet.create_transaction(values['recipient'], values['amount'], priv_key, unspent_txouts, tx_pool)

    if tx is not None:
        successfull = tx_pool.add_to_transaction_pool(tx, unspent_txouts)
        if successfull:
            response = {
                'new transaction': to_dict(tx)
            }
            return response, 201
    else:
        return "created transaction is not valid", 200

# create the genesis transaction
genesis_in = transaction.TxIn(txout_id="", txout_index=0, signature="")
address = "3059301306072a8648ce3d020106082a8648ce3d0301070342000447e45d57be90ac1ad97c5232f7922ade8e63f9931666f1fab5f1bcaac0bdc4b83bf68c72534eb33b68865b5e5465c7ba46094961b578513aed09ed22ab8c03f3"
genesis_out = transaction.TxOut(address=address, amount=50)
genesis_transaction = transaction.Transaction(txins=[genesis_in], txouts=[genesis_out])

# create the genesis block
genesis_hash = "0000607e58623c07e2634999e38638e13b76af5b450cd7a295bc60179e6db208"
genesis_block = blockchain.Block(index=0, hash=genesis_hash, previous_hash="", timestamp="inthebeninging", proof=33, data=[genesis_transaction])

# create the blockchain
block_chain = blockchain.Blockchain(genesis_block)

# create the transaction pool
tx_pool = transaction_pool.TransactionPool([])

# create the unspent transactions list
block_index = 0
unspent_txouts = transaction.process_transactions(block_chain.chain[block_index].data, [], block_index)

# create the wallet for this node
node_wallet = 'bobby_wallet'
wallet.init_wallet(node_wallet)
priv_key = wallet.get_key_from_wallet(node_wallet)
pub_key = priv_key.public_key()
node_address = wallet.get_hex_from_key(pub_key)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)