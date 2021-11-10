# Create Blockchain
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set();
    
    def create_block(self, proof, previous_hash):
        block = { 'index': len(self.chain) + 1,
                  'proof': proof,
                  'timestamp': str(datetime.datetime.now()),
                  'previous_hash': previous_hash,
                  'transactions': self.transactions
            }
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_last_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof ):
        proof = 1
        is_solved =  False
        while is_solved == False:
            hash_block = hashlib.sha256(str(proof**3 - previous_proof**2).encode()).hexdigest()
            if hash_block.startswith('0000'):
                is_solved = True
            else:
                proof+=1
        return proof
    
    def hash(self,block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def check_chain(self, chain):
        start = chain[0]
        index = 1
        while index < len(chain):
            current = chain[index]
            if current['previous_hash'] != self.hash(start):
                return False
            previous_proof = start['proof']
            proof = current['proof']
            hash_block = hashlib.sha256(str(proof**3 - previous_proof**2).encode()).hexdigest()
            if hash_block[:4] != '0000':
                return False
            start = current
            index+=1 
        return True
    
    def show_proof(self, num):
        previous_proof = self.chain[int(num)-1]['proof']
        proof = self.chain[int(num)]['proof']
        return hashlib.sha256(str(proof**3 - previous_proof**2).encode()).hexdigest()
    
    def get_block(self, num):
        return self.chain[num]
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender, 'receiver': receiver, 'amount': amount})
        last_block = self.get_last_block()
        return last_block['index']+1
    
    def add_node(self, address):
        self.nodes.add(urlparse(address).netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == '200':
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.check_chain(self, chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
        
                    
node_address = str(uuid4()).replace("-","")
           


app = Flask(__name__)

blockchain = Blockchain()


@app.route('/submit_transaction', methods = ['POST'])
def submit_transaction(args):
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Bad Request - Missing Keys', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'Success: Transaction added to block {index}'}
    return jsonify(response), 200

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    last_block = blockchain.get_last_block()
    new_proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.add_transaction(sender = node_address, receiver = 'Hadelin' , amount = 10)
    new_block = blockchain.create_block(new_proof,blockchain.hash(last_block))
    response = {'message':'You got a block',
                'index': new_block['index'],
                'proof': new_block['proof'],
                'timestamp':new_block['timestamp'],
                'previous_hash': new_block['previous_hash'],
                'transactions': new_block['transactions'] ,
                }
    return jsonify(response), 200

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
        }
    return jsonify(response), 200

@app.route('/check_block/<block_num>', methods = ['GET'])
def check_block(block_num):
    response = {
            'block_proof': blockchain.get_block(int(block_num)),
            'poW': blockchain.show_proof(block_num)
        }
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    valid = blockchain.check_chain(blockchain.chain)
    response = {
        'message': str(valid)}
    return jsonify(response), 200

@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No nodes!', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'Nodes succesfully added', 
                'total_nodes': list(blockchain.nodes) }
    return jsonify(response), 201


@app.route('/', defaults={'u_path': ''})
@app.route('/<path:u_path>')
def return_404(u_path):
    response= {"message": 'Oops -- nothing to be found here!'}
    return jsonify(response), 404


@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'chain replaced!',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'no change needed!'}
    return jsonify(response), 200




                
app.run(host = '0.0.0.0', port = 5003)


    
            
        
    
    
    
    
        
        
        
            

        
    
    
        
        