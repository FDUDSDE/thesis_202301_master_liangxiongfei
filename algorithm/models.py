import argparse
import os
import numpy as np
import math

import torchvision.transforms as transforms
from torchvision.utils import save_image
from torch.utils.data import DataLoader
from torchvision import datasets
from torch.autograd import Variable
import torch.autograd as autograd
from timm.models.layers import DropPath
import torch.nn as nn
import torch.nn.functional as F
import torch
from PIL import Image, ImageDraw, ImageOps
import torch.nn.utils.spectral_norm as spectral_norm


def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


def add_pool(x, nd_to_sample):
    dtype, device = x.dtype, x.device
    batch_size = torch.max(nd_to_sample) + 1
    pooled_x = torch.zeros(batch_size, x.shape[-1]).float().to(device)
    pool_to = nd_to_sample.view(-1, 1).expand_as(x).to(device)
    pooled_x = pooled_x.scatter_add(0, pool_to, x)
    return pooled_x


def compute_gradient_penalty(D, x, x_fake, given_y=None, given_w=None, \
                             nd_to_sample=None, data_parallel=None, \
                             ed_to_sample=None):
    indices = nd_to_sample, ed_to_sample
    batch_size = torch.max(nd_to_sample) + 1
    n_room = nd_to_sample.size(0)
    dtype, device = x.dtype, x.device
    u = torch.FloatTensor(x.shape[0], 1, 1).to(device)
    u.data.resize_(x.shape[0], 1, 1)
    u.uniform_(0, 1)
    x_both = x.data * u + x_fake.data * (1 - u)
    x_both = x_both.to(device)
    x_both = Variable(x_both, requires_grad=True)
    grad_outputs = torch.ones(batch_size, 1).to(device)
    grad_outputs_local = torch.ones(n_room, 1).to(device)
    if data_parallel:
        _output = data_parallel(D, (x_both, given_y, given_w, nd_to_sample), indices)
    else:
        _output = D(x_both, given_y, given_w, nd_to_sample)
    grad = torch.autograd.grad(outputs=_output, inputs=x_both, grad_outputs=grad_outputs, \
                               retain_graph=True, create_graph=True, only_inputs=True)[0]
    gradient_penalty = ((grad.norm(2, 1).norm(2, 1) - 1) ** 2).mean()
    return gradient_penalty


def compute_gradient_penalty_local(D_local, x, x_fake, given_y=None, given_w=None, \
                                   nd_to_sample=None, data_parallel=None, \
                                   ed_to_sample=None):
    indices = nd_to_sample, ed_to_sample
    batch_size = torch.max(nd_to_sample) + 1
    n_room = nd_to_sample.size(0)
    dtype, device = x.dtype, x.device
    u = torch.FloatTensor(x.shape[0], 1, 1).to(device)
    u.data.resize_(x.shape[0], 1, 1)
    u.uniform_(0, 1)
    x_both = x.data * u + x_fake.data * (1 - u)
    x_both = x_both.to(device)
    x_both = Variable(x_both, requires_grad=True)
    grad_outputs_local = torch.ones(n_room, 1).to(device)
    if data_parallel:
        _output_local = data_parallel(D_local, (x_both, given_y, nd_to_sample), indices)
    else:
        _output_local = D_local(x_both, given_y, nd_to_sample)
    grad_local = torch.autograd.grad(outputs=_output_local, inputs=x_both, grad_outputs=grad_outputs_local, \
                                     retain_graph=True, create_graph=True, only_inputs=True)[0]
    gradient_penalty_local = ((grad_local.norm(2, 1).norm(2, 1) - 1) ** 2).mean()
    return gradient_penalty_local


def conv_block(in_channels, out_channels, k, s, p, act=None, upsample=False, spec_norm=False, batch_norm=False):
    block = []

    if upsample:
        if spec_norm:
            block.append(spectral_norm(torch.nn.ConvTranspose2d(in_channels, out_channels, \
                                                                kernel_size=k, stride=s, \
                                                                padding=p, bias=True)))
        else:
            block.append(torch.nn.ConvTranspose2d(in_channels, out_channels, \
                                                  kernel_size=k, stride=s, \
                                                  padding=p, bias=True))
    else:
        if spec_norm:
            block.append(spectral_norm(torch.nn.Conv2d(in_channels, out_channels, \
                                                       kernel_size=k, stride=s, \
                                                       padding=p, bias=True)))
        else:
            block.append(torch.nn.Conv2d(in_channels, out_channels, \
                                         kernel_size=k, stride=s, \
                                         padding=p, bias=True))
    if batch_norm:
        block.append(nn.BatchNorm2d(out_channels))
    if "leaky" in act:
        block.append(torch.nn.LeakyReLU(0.1, inplace=True))
    elif "relu" in act:
        block.append(torch.nn.ReLU(inplace=True))
    # elif "tanh":
    #     block.append(torch.nn.Tanh())
    return block


# Convolutional Message Passing
class CMP(nn.Module):
    def __init__(self, in_channels):
        super(CMP, self).__init__()
        self.in_channels = in_channels
        self.encoder = nn.Sequential(
            *conv_block(3 * in_channels, 2 * in_channels, 3, 1, 1, act="leaky"),
            *conv_block(2 * in_channels, 2 * in_channels, 3, 1, 1, act="leaky"),
            *conv_block(2 * in_channels, in_channels, 3, 1, 1, act="leaky"))

    def forward(self, feats, edges=None):
        # allocate memory
        dtype, device = feats.dtype, feats.device
        edges = edges.view(-1, 3)
        V, E = feats.size(0), edges.size(0)
        pooled_v_pos = torch.zeros(V, feats.shape[-3], feats.shape[-1], feats.shape[-1], dtype=dtype, device=device)
        pooled_v_neg = torch.zeros(V, feats.shape[-3], feats.shape[-1], feats.shape[-1], dtype=dtype, device=device)
        # pool positive edges
        pos_inds = torch.where(edges[:, 1] > 0)
        pos_v_src = torch.cat([edges[pos_inds[0], 0], edges[pos_inds[0], 2]]).long()
        pos_v_dst = torch.cat([edges[pos_inds[0], 2], edges[pos_inds[0], 0]]).long()
        pos_vecs_src = feats[pos_v_src.contiguous()]
        pos_v_dst = pos_v_dst.view(-1, 1, 1, 1).expand_as(pos_vecs_src).to(device)
        pooled_v_pos = torch.scatter_add(pooled_v_pos, 0, pos_v_dst, pos_vecs_src)

        # pool negative edges
        neg_inds = torch.where(edges[:, 1] < 0)
        neg_v_src = torch.cat([edges[neg_inds[0], 0], edges[neg_inds[0], 2]]).long()
        neg_v_dst = torch.cat([edges[neg_inds[0], 2], edges[neg_inds[0], 0]]).long()
        neg_vecs_src = feats[neg_v_src.contiguous()]
        neg_v_dst = neg_v_dst.view(-1, 1, 1, 1).expand_as(neg_vecs_src).to(device)
        pooled_v_neg = torch.scatter_add(pooled_v_neg, 0, neg_v_dst, neg_vecs_src)
        # update nodes features
        enc_in = torch.cat([feats, pooled_v_pos, pooled_v_neg], 1)
        out = self.encoder(enc_in)
        return out


class SelfAttention(nn.Module):
    def __init__(self, in_dim, activation):
        super(SelfAttention, self).__init__()
        self.channel_in = in_dim
        self.activation = activation
        self.query_conv = nn.Conv2d(in_channels=in_dim, out_channels=in_dim // 8, kernel_size=1)
        self.key_conv = nn.Conv2d(in_channels=in_dim, out_channels=in_dim // 8, kernel_size=1)
        self.value_conv = nn.Conv2d(in_channels=in_dim, out_channels=in_dim, kernel_size=1)
        self.gamma = nn.Parameter(torch.zeros(1))
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        m_batchsize, C, width, height = x.size()
        proj_query = self.query_conv(x).view(m_batchsize, -1, width * height).permute(0, 2, 1)
        proj_key = self.key_conv(x).view(m_batchsize, -1, width * height)
        energy = torch.bmm(proj_query, proj_key)
        attention = self.softmax(energy)
        proj_value = self.value_conv(x).view(m_batchsize, -1, width*height)
        out = torch.bmm(proj_value, attention.permute(0, 2, 1))
        out = out.view(m_batchsize, C, width, height)
        out = self.gamma*out + x
        return out


class Generator(nn.Module):
    def __init__(self):
        super(Generator, self).__init__()
        self.init_size = 32 // 4
        self.l1 = nn.Sequential(nn.Linear(146, 16 * self.init_size ** 2))  # 146
        self.upsample_1 = nn.Sequential(*conv_block(16, 16, 4, 2, 1, act="leaky", upsample=True))
        self.upsample_2 = nn.Sequential(*conv_block(16, 16, 4, 2, 1, act="leaky", upsample=True))
        self.upsample_3 = nn.Sequential(*conv_block(16, 16, 4, 2, 1, act="leaky", upsample=True))
        self.cmp_1 = CMP(in_channels=16)
        self.cmp_2 = CMP(in_channels=16)
        self.cmp_3 = CMP(in_channels=16)
        self.cmp_4 = CMP(in_channels=16)
        self.decoder = nn.Sequential(
            *conv_block(16, 256, 3, 1, 1, act="leaky"),
            *conv_block(256, 128, 3, 1, 1, act="leaky"),
            *conv_block(128, 1, 3, 1, 1, act="tanh"))
        # for finetuning
        self.l1_fixed = nn.Sequential(nn.Linear(1, 1 * self.init_size ** 2))
        self.enc_1 = nn.Sequential(
            *conv_block(2, 32, 3, 2, 1, act="leaky"),
            *conv_block(32, 32, 3, 2, 1, act="leaky"),
            *conv_block(32, 16, 3, 2, 1, act="leaky"))
        self.enc_2 = nn.Sequential(
            *conv_block(32, 32, 3, 1, 1, act="leaky"),
            *conv_block(32, 16, 3, 1, 1, act="leaky"))
        # self.atten1 = SelfAttention(32, 'relu')
        # self.atten2 = SelfAttention(16, 'relu')

    def forward(self, z, given_m=None, given_y=None, given_w=None, given_v=None):
        z = z.view(-1, 128)
        # include nodes
        y = given_y.view(-1, 18)
        z = torch.cat([z, y], 1)
        x = self.l1(z)
        f = x.view(-1, 16, self.init_size, self.init_size)
        # combine masks and noise vectors
        m = self.enc_1(given_m)
        f = torch.cat([f, m], 1)
        # f = self.atten1(f)
        f = self.enc_2(f)
        # f = self.atten2(f)
        # apply Conv-MPN
        x = self.cmp_1(f, given_w).view(-1, *f.shape[1:])
        x = self.upsample_1(x)
        x = self.cmp_2(x, given_w).view(-1, *x.shape[1:])
        x = self.upsample_2(x)
        x = self.cmp_3(x, given_w).view(-1, *x.shape[1:])
        x = self.upsample_3(x)
        x = self.cmp_4(x, given_w).view(-1, *x.shape[1:])
        x = self.decoder(x.view(-1, x.shape[1], *x.shape[2:]))
        x = x.view(-1, *x.shape[2:])
        return x


class GeneratorLocal(nn.Module):
    def __init__(self):
        super(GeneratorLocal, self).__init__()
        self.init_size = 32 // 4
        self.l1 = nn.Sequential(nn.Linear(146, 16 * self.init_size ** 2))
        self.enc_1 = nn.Sequential(
            *conv_block(16, 32, 3, 2, 1, act="leaky"),
            *conv_block(32, 32, 3, 2, 1, act="leaky"),
            *conv_block(32, 16, 3, 2, 1, act="leaky"))
        self.upsample_1 = nn.Sequential(
            *conv_block(16, 32, 4, 2, 1, act="leaky", upsample=True),
            *conv_block(32, 32, 4, 2, 1, act="leaky", upsample=True),
            *conv_block(32, 16, 4, 2, 1, act="leaky", upsample=True))
        self.decoder = nn.Sequential(
            *conv_block(16, 256, 3, 1, 1, act="leaky"),
            *conv_block(256, 128, 3, 1, 1, act="leaky"),
            *conv_block(128, 1, 3, 1, 1, act="tanh"))

    def forward(self, z, given_m=None, given_y=None):
        z = z.view(-1, 128)
        y = given_y.view(-1, 18)
        z = torch.cat([z, y], 1)
        x = self.l1(z)
        f = x.view(-1, 16, self.init_size, self.init_size)
        # x = self.enc_1(f)
        x = self.upsample_1(f)
        x = self.decoder(x)
        return x


class Discriminator(nn.Module):
    def __init__(self):
        super(Discriminator, self).__init__()
        self.encoder = nn.Sequential(
            *conv_block(9, 16, 3, 1, 1, act="leaky"),
            *conv_block(16, 16, 3, 1, 1, act="leaky"),
            *conv_block(16, 16, 3, 1, 1, act="leaky"),
            *conv_block(16, 16, 3, 1, 1, act="leaky"))
        self.l1 = nn.Sequential(nn.Linear(18, 8 * 64 ** 2))
        self.cmp_1 = CMP(in_channels=16)
        self.downsample_1 = nn.Sequential(*conv_block(16, 16, 3, 2, 1, act="leaky"))
        self.cmp_2 = CMP(in_channels=16)
        self.downsample_2 = nn.Sequential(*conv_block(16, 16, 3, 2, 1, act="leaky"))
        self.cmp_3 = CMP(in_channels=16)
        self.downsample_3 = nn.Sequential(*conv_block(16, 16, 3, 2, 1, act="leaky"))
        self.cmp_4 = CMP(in_channels=16)

        self.decoder = nn.Sequential(
            *conv_block(16, 256, 3, 2, 1, act="leaky"),
            *conv_block(256, 128, 3, 2, 1, act="leaky"),
            *conv_block(128, 128, 3, 2, 1, act="leaky"))
        # The height and width of downsampled image
        ds_size = 32 // 2 ** 4
        self.fc_layer_global = nn.Sequential(nn.Linear(128, 1))
        self.fc_layer_local = nn.Sequential(nn.Linear(128, 1))
        self.act = nn.Sigmoid()
        self.atten1 = SelfAttention(9, 'relu')
        self.atten2 = SelfAttention(16, 'relu')

    def forward(self, x, given_y=None, given_w=None, nd_to_sample=None):
        x = x.view(-1, 1, 64, 64)

        # include nodes
        y = given_y
        y = self.l1(y)
        y = y.view(-1, 8, 64, 64)
        x = torch.cat([x, y], 1)
        # message passing -- Conv-MPN
        x = self.atten1(x)
        x = self.encoder(x)
        x = self.atten2(x)
        x = self.cmp_1(x, given_w).view(-1, *x.shape[1:])
        x = self.downsample_1(x)
        x = self.cmp_2(x, given_w).view(-1, *x.shape[1:])
        x = self.downsample_2(x)
        x = self.cmp_3(x, given_w).view(-1, *x.shape[1:])
        x = self.downsample_3(x)
        x = self.cmp_4(x, given_w).view(-1, *x.shape[1:])
        x = self.decoder(x.view(-1, x.shape[1], *x.shape[2:]))
        x = x.view(-1, x.shape[1])
        # global loss
        x_g = add_pool(x, nd_to_sample)
        validity_global = self.fc_layer_global(x_g)
        return validity_global

class AutoEncoder(nn.Module):
    def __init__(self):
        super(AutoEncoder, self).__init__()
        self.enc = nn.Sequential(
            *conv_block(1, 16, 3, 2, 1, act="leaky"),
            *conv_block(16, 16, 3, 2, 1, act="leaky"),
            *conv_block(16, 16, 3, 2, 1, act="leaky"),
            *conv_block(16, 16, 3, 2, 1, act="leaky"))
        self.dec = self.upsample_1 = nn.Sequential(
            *conv_block(16, 32, 4, 2, 1, act="leaky", upsample=True),
            *conv_block(32, 32, 4, 2, 1, act="leaky", upsample=True),
            *conv_block(32, 16, 4, 2, 1, act="leaky", upsample=True),
            *conv_block(16, 1, 4, 2, 1, act="leaky", upsample=True))
    def forward(self, x):
        return self.dec(self.enc(x))

class ResidualBlock(nn.Module):
    def __init__(self, in_features, out_features):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=in_features, out_channels=out_features, kernel_size=3, stride=1, padding=1,
                               bias=False)
        self.bn1 = nn.BatchNorm2d(out_features)
        self.relu1 = nn.LeakyReLU(0.2)
        self.conv2 = nn.Conv2d(in_channels=out_features, out_channels=in_features, kernel_size=3, stride=1, padding=1,
                               bias=False)
        self.bn2 = nn.BatchNorm2d(in_features)

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu1(out)
        out = self.conv2(out)
        out = self.bn2(out)
        return x + out


class DiscriminatorLocal(nn.Module):
    def __init__(self):
        super(DiscriminatorLocal, self).__init__()
        self.encoder = nn.Sequential(
            *conv_block(9, 16, 3, 2, 1, act='leaky'),
            ResidualBlock(16, 32),
            *conv_block(16, 32, 3, 2, 1, act='leaky'),
            *conv_block(32, 64, 3, 2, 1, act='leaky'),
            ResidualBlock(64, 128),
            *conv_block(64, 128, 3, 2, 1, act='leaky'),
            *conv_block(128, 256, 3, 2, 1, act='leaky'),
            ResidualBlock(256, 512),
            *conv_block(256, 256, 3, 2, 1, act='leaky'),
            *conv_block(256, 128, 3, 2, 1, act='leaky'),
        )
        self.l1 = nn.Sequential(nn.Linear(18, 8 * 64 ** 2))
        self.fc_layer_local = nn.Sequential(nn.Linear(128, 1))
        self.atten1 = SelfAttention(8, 'relu')
        self.atten2 = SelfAttention(9, 'relu')

    def forward(self, x, nds=None, nd_to_sample=None):
        x = x.view(-1, 1, 64, 64)
        y = self.l1(nds)
        y = y.view(-1, 8, 64, 64)
        y = self.atten1(y)
        x = torch.cat([x, y], 1)
        x = self.atten2(x)
        x = self.encoder(x)
        x = x.view(-1, x.shape[1])
        # x_g = add_pool(x, nd_to_sample)
        x_g = self.fc_layer_local(x)
        return x_g
