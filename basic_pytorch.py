#!/usr/bin/env python

import argparse
from singen import SinGen

import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable


lstm_timesteps = 22  # lstm timesteps is how big to train on
lstm_batchsize = 128
lstm_units = 64


class State(object):
    def __init__(self, h=None, c=None):
        self.h = h
        self.c = c

    def state(self):
        return (self.h, self.c)

    def update(self, h, c):
        self.h = h
        self.c = c

    @staticmethod
    def from_params(inputs, outputs):
        s = State()
        s.h = Variable(torch.zeros(inputs, outputs).double(), requires_grad=False)
        s.c = Variable(torch.zeros(inputs, outputs).double(), requires_grad=False)
        return s


class TSModel(nn.Module):
    def __init__(self, timesteps, batchsize):
        super().__init__()
        self.c0 = nn.LSTMCell(1, lstm_units)
        self.c1 = nn.LSTMCell(lstm_units, 1)
        self.double()

    def forward(self, input, future=0):
        '''input is size (batches, timesteps)
           data looks like this:
           [sin(tA), sin(tA+1), sin(tA+2),... sin(tA+N)],
           [sin(tB), sin(tB+1), sin(tB+2),... sin(tB+N)],

           where A,B... in random(batches)
        '''
        outputs = []
        state = []
        state.append(State.from_params(input.size(0), lstm_units))
        state.append(State.from_params(input.size(0), 1))

        for i, input_t in enumerate(input.chunk(input.size(1), dim=1)):
            h, c = self.c0(input_t, state[0].state())
            state[0].update(h, c)
            h, c = self.c1(c, state[1].state())
            state[1].update(h, c)
            outputs += [c]
        outputs = torch.stack(outputs, 1).squeeze(2)
        return outputs


def train(m, epochs, lr, batchsize):
    optimizer = optim.Adam(m.parameters(), lr=lr)
    criterion = nn.MSELoss()

    g = SinGen(timesteps=lstm_timesteps, batchsize=batchsize)

    for i in range(epochs):
        print('------------------------------------------')
        print(i)
        print('------------------------------------------')
        x, y = g.batch()

        x = Variable(torch.from_numpy(x.squeeze()), requires_grad=False)
        y = Variable(torch.from_numpy(y.squeeze()), requires_grad=False)

        optimizer.zero_grad()
        output = m(x)
        loss = criterion(output, y)
        print("loss: ", loss.data.numpy()[0])

        loss.backward()
        optimizer.step()


def get_args():
    p = argparse.ArgumentParser("Train Pytorch LSTM Model for sine wave")
    # p.add_argument('--save', help="h5 file to save model to when done")
    return p.parse_args()


def main():
    get_args()
    m = TSModel(timesteps=lstm_timesteps, batchsize=lstm_batchsize)
    train(m, 64, 1e-3, lstm_batchsize)
    train(m, 22, 1e-4, lstm_batchsize)
    train(m, 22, 1e-5, lstm_batchsize)


if __name__ == '__main__':
    main()