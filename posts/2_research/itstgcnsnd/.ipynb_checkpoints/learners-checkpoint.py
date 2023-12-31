import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

# torch
import torch
import torch.nn.functional as F
#import torch_geometric_temporal
# from torch_geometric_temporal.nn.recurrent import GConvGRU
# from torch_geometric_temporal.nn.recurrent import GConvLSTM
# from torch_geometric_temporal.nn.recurrent import GCLSTM
# from torch_geometric_temporal.nn.recurrent import DCRNN
# from torch_geometric_temporal.nn.recurrent import LRGCN
# from torch_geometric_temporal.nn.recurrent import TGCN
# from torch_geometric_temporal.nn.recurrent import EvolveGCNO
# from torch_geometric_temporal.nn.recurrent import DyGrEncoder
from torch_geometric_temporal.nn.recurrent import EvolveGCNH


# utils
import copy
#import time
#import pickle
#import itertools
#from tqdm import tqdm
#import warnings

# rpy2
#import rpy2
#import rpy2.robjects as ro 
from rpy2.robjects.vectors import FloatVector
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
import rpy2.robjects.numpy2ri as rpyn
GNAR = importr('GNAR') # import GNAR 
#igraph = importr('igraph') # import igraph 
ebayesthresh = importr('EbayesThresh').ebayesthresh

from .utils import convert_train_dataset
from .utils import DatasetLoader

def flatten_weight(T,N,ws,wt):
    Is = np.eye(N,N)
    lst = [[0]*T for t in range(T)]
    for i in range(T):
        for j in range(T):
            if i==j: 
                lst[i][j] = ws 
            elif abs(i-j)==1:
                lst[i][j] = Is
            else:
                lst[i][j] = Is*0
    return np.concatenate([np.concatenate(l,axis=1) for l in lst],axis=0) # TN*TN matrix

def make_Psi(T,N,edge_index,edge_weight):
    wt = np.zeros((T,T))
    for i in range(T):
        for j in range(T):
            if i==j :
                wt[i,j] = 0
            elif np.abs(i-j) <= 1 : 
                wt[i,j] = 1
    ws = np.zeros((N,N))
    for i in range(N):
        for j in range(edge_weight.shape[0]):
            if edge_index[0][j] == i :
                ws[i,edge_index[1][j]] = edge_weight[j]
    W = flatten_weight(T,N,ws,wt) # TN*TN matrix
    d = np.array(W.sum(axis=1))
    D = np.diag(d)
    L = np.array(np.diag(1/np.sqrt(d)) @ (D-W) @ np.diag(1/np.sqrt(d)))
    lamb, Psi = np.linalg.eigh(L)
    return Psi # TN*TN matrix

def trim(f,edge_index,edge_weight):
    f = np.array(f)
    if len(f.shape)==1: f = f.reshape(-1,1)
    T,N = f.shape # f = T*N matrix
    Psi = make_Psi(T,N,edge_index,edge_weight) # TN*TN matrix
    fbar = Psi.T @ f.reshape(-1,1) # TN*TN X TN*1 matrix = TN*1 matrix
    fbar_threshed = np.stack([ebayesthresh(FloatVector(fbar.reshape(-1,N)[:,i])) for i in range(N)],axis=1)
    fhat_flatten = Psi @ fbar_threshed.reshape(-1,1) # inverse dft 
    fhat = fhat_flatten.reshape(-1,N)
    return fhat

def update_from_freq_domain(signal, missing_index,edge_index,edge_weight):
    signal = np.array(signal)
    T,N = signal.shape 
    signal_trimed = trim(signal,edge_index,edge_weight)
    for i in range(N):
        try: 
            signal[missing_index[i],i] = signal_trimed[missing_index[i],i]
        except: 
            pass 
    return signal


# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = GConvGRU(node_features, filters, 2)
#         self.linear = torch.nn.Linear(filters, 1)

#     def forward(self, x, edge_index, edge_weight):
#         h = self.recurrent(x, edge_index, edge_weight)
#         h = F.relu(h)
#         h = self.linear(h)
#         return h

# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = GConvLSTM(in_channels = node_features, out_channels = filters, K = 2)
#         self.linear = torch.nn.Linear(filters, 1)

#     def forward(self, x, edge_index, edge_weight, h, c):
#         h_0, c_0 = self.recurrent(x, edge_index, edge_weight, h, c)
#         h = F.relu(h_0)
#         h = self.linear(h)
#         return h, h_0, c_0

# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = GCLSTM(node_features, filters, 1)
#         self.linear = torch.nn.Linear(filters, 1)

#     def forward(self, x, edge_index, edge_weight, h, c):
#         h_0, c_0 = self.recurrent(x, edge_index, edge_weight, h, c)
#         h = F.relu(h_0)
#         h = self.linear(h)
#         return h, h_0, c_0

# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = DCRNN(node_features, filters, 1)
#         self.linear = torch.nn.Linear(filters, 1)

#     def forward(self, x, edge_index, edge_weight):
#         h = self.recurrent(x, edge_index, edge_weight)
#         h = F.relu(h)
#         h = self.linear(h)
#         return h
    
# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = LRGCN(node_features, filters, 2, 1)
#         self.linear = torch.nn.Linear(filters, 1)

#     def forward(self, x, edge_index, edge_weight, h_0, c_0):
#         h_0, c_0 = self.recurrent(x, edge_index, edge_weight, h_0, c_0)
#         h = F.relu(h_0)
#         h = self.linear(h)
#         return h, h_0, c_0
    
# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = TGCN(node_features, filters)
#         self.linear = torch.nn.Linear(filters, 1)

#     def forward(self, x, edge_index, edge_weight, prev_hidden_state):
#         h = self.recurrent(x, edge_index, edge_weight, prev_hidden_state)
#         y = F.relu(h)
#         y = self.linear(y)
#         return y, h

# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = EvolveGCNO(node_features)
#         self.linear = torch.nn.Linear(node_features, 1)

#     def forward(self, x, edge_index, edge_weight):
#         h = self.recurrent(x, edge_index, edge_weight)
#         h = F.relu(h)
#         h = self.linear(h)
#         return h
    
# class RecurrentGCN(torch.nn.Module):
#     def __init__(self, node_features, filters):
#         super(RecurrentGCN, self).__init__()
#         self.recurrent = DyGrEncoder(conv_out_channels=node_features, conv_num_layers=1, conv_aggr="mean", lstm_out_channels=filters, lstm_num_layers=1)
#         self.linear = torch.nn.Linear(filters, 1)

#     def forward(self, x, edge_index, edge_weight, h_0, c_0):
#         h, h_0, c_0 = self.recurrent(x, edge_index, edge_weight, h_0, c_0)
#         h = F.relu(h)
#         h = self.linear(h)
#         return h, h_0, c_0

class RecurrentGCN(torch.nn.Module):
    def __init__(self, num_of_nodes, node_features, filters):
        super(RecurrentGCN, self).__init__()
        self.recurrent = EvolveGCNH(num_of_nodes, node_features)
        self.linear = torch.nn.Linear(node_features, 1)

    def forward(self, x, edge_index, edge_weight):
        h = self.recurrent(x, edge_index, edge_weight)
        h = F.relu(h)
        h = self.linear(h)
        return h
    
    
class StgcnLearner:
    def __init__(self,train_dataset,dataset_name = None):
        self.train_dataset = train_dataset
        self.lags = torch.tensor(train_dataset.features).shape[-1]
        self.dataset_name = str(train_dataset) if dataset_name is None else dataset_name
        self.mindex= getattr(self.train_dataset,'mindex',None)
        self.mrate_eachnode = getattr(self.train_dataset,'mrate_eachnode',0)
        self.mrate_total = getattr(self.train_dataset,'mrate_total',0)
        self.mtype = getattr(self.train_dataset,'mtype',None)
        self.interpolation_method = getattr(self.train_dataset,'interpolation_method',None)
        self.method = 'STGCN'
        self.N = np.array(train_dataset.features).shape[1]
        
    def learn(self,filters=32,epoch=50):
        # self.model = RecurrentGCN(node_features=self.lags, filters=filters)
        self.model = RecurrentGCN(num_of_nodes=self.N,node_features=self.lags, filters=filters)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        self.model.train()
        for e in range(epoch):
            
            cost = 0
            for t, snapshot in enumerate(self.train_dataset):
                y_hat = self.model(snapshot.x, snapshot.edge_index, snapshot.edge_attr).reshape(-1)
                cost = cost + torch.mean((y_hat-snapshot.y)**2)
            cost = cost / (t+1)
            cost.backward()
            self.optimizer.step()
            self.optimizer.zero_grad()
            print('{}/{}'.format(e+1,epoch),end='\r')
        # recording HP
        self.nof_filters = filters
        self.epochs = epoch+1
    def __call__(self,dataset):
        X = torch.tensor(dataset.features).float()
        y = torch.tensor(dataset.targets).float()
        yhat = torch.stack([self.model(snapshot.x, snapshot.edge_index, snapshot.edge_attr) for snapshot in dataset]).detach().squeeze().float()
        # yhat = torch.stack([self.model(snapshot.x, snapshot.edge_index, snapshot.edge_attr, self.h, self.c)[0] for snapshot in dataset]).detach().squeeze().float()
        # yhat = torch.stack([self.model(snapshot.x, snapshot.edge_index, snapshot.edge_attr,self.hidden_state)[0] for snapshot in dataset]).detach().squeeze().float()
        return {'X':X, 'y':y, 'yhat':yhat} 

class ITStgcnLearner(StgcnLearner):
    def __init__(self,train_dataset,dataset_name = None):
        super().__init__(train_dataset)
        self.method = 'IT-STGCN'
    def learn(self,filters=32,epoch=50):
        # self.model = RecurrentGCN(node_features=self.lags, filters=filters)
        self.model = RecurrentGCN(num_of_nodes=self.N,node_features=self.lags, filters=filters)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        self.model.train()
        train_dataset_temp = copy.copy(self.train_dataset)
        for e in range(epoch):
            f,lags = convert_train_dataset(train_dataset_temp)
            f = update_from_freq_domain(f,self.mindex,self.train_dataset.edge_index,self.train_dataset.edge_weight)
            T,N = f.shape 
            data_dict_temp = {
                'edges':self.train_dataset.edge_index.T.tolist(), 
                'node_ids':{'node'+str(i):i for i in range(N)}, 
                'FX':f
            }
            train_dataset_temp = DatasetLoader(data_dict_temp).get_dataset(lags=self.lags)  
            cost = 0
            for t, snapshot in enumerate(train_dataset_temp):
                y_hat = self.model(snapshot.x, snapshot.edge_index, snapshot.edge_attr).reshape(-1)
                cost = cost + torch.mean((y_hat-snapshot.y)**2)
            cost = cost / (t+1)
            cost.backward()
            self.optimizer.step()
            self.optimizer.zero_grad()
            print('{}/{}'.format(e+1,epoch),end='\r')
        # record
        self.nof_filters = filters
        self.epochs = epoch+1

class GNARLearner(StgcnLearner):
    def __init__(self,train_dataset,dataset_name = None):
        super().__init__(train_dataset)
        self.method = 'GNAR'
    def learn(self):
    
        self.N = np.array(self.train_dataset.features).shape[1]
        w=np.zeros((self.N,self.N))
        for k in range(len(self.train_dataset.edge_index[0])):
            w[self.train_dataset.edge_index[0][k],self.train_dataset.edge_index[1][k]] = 1

        self.m = robjects.r.matrix(FloatVector(w), nrow = self.N, ncol = self.N)
        _vts = robjects.r.matrix(
            rpyn.numpy2rpy(np.array(self.train_dataset.features).reshape(-1,1).squeeze()), 
            nrow = np.array(self.train_dataset.targets).shape[0] + self.lags, 
            ncol = self.N
        )
        self.fit = GNAR.GNARfit(vts=_vts,net = GNAR.matrixtoGNAR(self.m), alphaOrder = self.lags, betaOrder = FloatVector([1]*self.lags))
        
        self.nof_filters = None
        self.epochs = None
    def __call__(self,dataset,mode='fit',n_ahead=1):
        r_code = '''
        substitute<-function(lrnr_fit1,lrnr_fit2){
        lrnr_fit1$mod$coef = lrnr_fit2$mod$coef
        return(lrnr_fit1)
        }
        '''
        robjects.r(r_code)
        substitute=robjects.globalenv['substitute']
        _vts = robjects.r.matrix(
            rpyn.numpy2rpy(np.array(dataset.features).reshape(-1,1).squeeze()), 
            nrow = np.array(dataset.targets).shape[0] + self.lags, 
            ncol = self.N
        )
        self._fit = GNAR.GNARfit(vts = _vts, net = GNAR.matrixtoGNAR(self.m), alphaOrder = self.lags, betaOrder = FloatVector([1]*self.lags))
        self._fit = substitute(self._fit,self.fit)
        
        X = torch.tensor(dataset.features).float()
        y = torch.tensor(dataset.targets).float()
        if mode == 'fit':
            X = np.array(dataset.features)
            yhat = GNAR.fitted_GNARfit(self._fit,robjects.FloatVector(X))
            X = torch.tensor(X).float()
            yhat = torch.tensor(np.array(yhat)).float()
        elif mode == 'fore': 
            yhat = GNAR.predict_GNARfit(self.fit,n_ahead=n_ahead)
            yhat = torch.tensor(np.array(yhat)).float()
        else: 
            print('mode should be "fit" or "fore"')
        return {'X':X, 'y':y, 'yhat':yhat} 