# encoding: utf-8
"""
Author: zhengchuanpan
GitHub: https://github.com/zhengchuanpan/GMAN
"""
from . import node2vec
import numpy as np
import networkx as nx
from gensim.models import Word2Vec


class SEDataHelper:
    def __init__(self, is_directed, p, q, 
                 num_walks, walk_length, dimensions, 
                 window_size, itertime, Adj_file, SE_file):

        self.is_directed = is_directed
        self.p = p
        self.q = q
        self.num_walks = num_walks
        self.walk_length = walk_length
        self.dimensions = dimensions
        self.window_size = window_size
        self.itertime = itertime
        self.Adj_file = Adj_file
        self.SE_file = SE_file

    def read_graph(self, edgelist_file):
        G = nx.read_edgelist(
            edgelist_file, nodetype=int, data=(('weight',float),),
            create_using=nx.DiGraph())

        return G

    def learn_embeddings(self, walks, dimensions, itertime, output_file,):
        walks = [list(map(str, walk)) for walk in walks]
        model = Word2Vec(
                walks,
                vector_size = dimensions, # size
                window = self.window_size,
                min_count = 0,
                sg=1,
                workers = 8,
                epochs = itertime # iter
            )
        model.wv.save_word2vec_format(output_file)
        
        return

    def run(self):
        nx_G = self.read_graph(edgelist_file = self.Adj_file)

        G = node2vec.Graph(nx_G, self.is_directed, self.p, self.q)

        G.preprocess_transition_probs() # Wall time: 1min 13s

        walks = G.simulate_walks(self.num_walks, self.walk_length) # Wall time: 28.1 s

        self.learn_embeddings(
                walks,
                dimensions=self.dimensions,
                itertime=self.itertime,
                output_file=self.SE_file
            ) 

if __name__ == "__main__":
    train_node2vec = SEDataHelper(
            is_directed=True, p=2, q=1, 
            num_walks=100, walk_length=80,
            dimensions=64, window_size=10,
            itertime=1000,
            Adj_file='../train data/SE/Adj.txt',
            SE_file='../train data/SE/SE.txt'
        )

    train_node2vec.run()