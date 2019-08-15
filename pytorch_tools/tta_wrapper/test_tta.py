import torch
import pytest
from pytorch_tools.tta_wrapper import functional as F
from .wrappers import TTA_Wrapper
#import numpy as np
#from pytorch_toolbelt.utils.torch_utils import to_numpy
from torch import nn


class NoOp(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, input):
        return input


class SumAll(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, input):
        return input.sum(dim=[1, 2, 3])

#INPUT = torch.arange(1*1*4*4).reshape((1,1,4,4))
INPUT = torch.Tensor([[[[ 0,  1,  2,  3],
                        [ 4,  5,  6,  7],
                        [ 8,  9, 10, 11],
                        [12, 13, 14, 15]]]]).type(torch.float)

def test_hflip():
    expected = torch.Tensor([[[[12, 13, 14, 15],
                               [ 8,  9, 10, 11],
                               [ 4,  5,  6,  7],
                               [ 0,  1,  2,  3]]]])
    assert expected.allclose(F.HFlip().forward(INPUT, 1))
    assert expected.allclose(F.HFlip().backward(INPUT, 1))
    assert INPUT.allclose(F.HFlip().forward(INPUT, 0))

def test_vflip():
    expected = torch.Tensor([[[[ 3,  2,  1,  0],
                               [ 7,  6,  5,  4],
                               [11, 10,  9,  8],
                               [15, 14, 13, 12]]]])
    assert expected.allclose(F.VFlip().forward(INPUT, 1))
    assert INPUT.allclose(F.VFlip().forward(INPUT, 0))                 

def test_hshift():
    expected = torch.Tensor([[[[ 3,  0,  1,  2],
                               [ 7,  4,  5,  6],
                               [11,  8,  9, 10],
                               [15, 12, 13, 14]]]])

    forward = F.HShift().forward(INPUT, 1)
    assert expected.allclose(forward)
    assert INPUT.allclose(F.HShift().backward(forward, 1))

def test_vshift():
    expected = torch.Tensor([[[[12, 13, 14, 15],
                               [ 0,  1,  2,  3],
                               [ 4,  5,  6,  7],
                               [ 8,  9, 10, 11]]]])
    forward = F.VShift().forward(INPUT, 1) 
    assert expected.allclose(forward)
    assert INPUT.allclose(F.VShift().backward(forward, 1))

def test_add():
    expected = INPUT + 2
    assert expected.allclose(F.Add().forward(INPUT, 2))
    
def test_multiply():
    expected = INPUT * 1.1
    assert expected.allclose(F.Multiply().forward(INPUT, 1.1))

def test_rotate():
    expected = torch.Tensor([[[[ 3.,  7., 11., 15.],
                            [ 2.,  6., 10., 14.],
                            [ 1.,  5.,  9., 13.],
                            [ 0.,  4.,  8., 12.]]]])
    forward =  F.Rotate().forward(INPUT, 90)
    assert expected.allclose(forward)
    assert INPUT.allclose(F.Rotate().backward(forward, 90))

@pytest.mark.parametrize('merge', ['gmean','max', 'gmean'])
def test_wrapper_segm(merge):
    m = NoOp()
    inp = INPUT / 15. # make sure max is less that 1 to avoid overflow                    
    tta_m = TTA_Wrapper(m, segm=True, h_flip=True, v_flip=True, h_shift=1, v_shift=-1, rotation=90, merge=merge) 
    assert (inp - tta_m(inp)).mean() < 1e-6
    
@pytest.mark.parametrize('merge', ['mean', 'max', 'gmean'])
def test_wrapper_cls(merge):
    m = SumAll()
    inp = INPUT / 15. # make sure max is less that 1 to avoid overflow        
    tta_m = TTA_Wrapper(m, segm=False, h_flip=True, v_flip=True, h_shift=1, v_shift=-1, rotation=90, merge=merge)
    assert tta_m(inp).allclose(torch.Tensor([8.]))
