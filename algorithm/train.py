import argparse
import json
import os
import time

import numpy as np
import math
from FloorplanDataset import FloorplanDataset, floorplan_collate_fn
import torchvision.transforms as transforms
from torchvision.utils import save_image
from torch.utils.data import DataLoader
from torchvision import datasets
from torch.autograd import Variable
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F
import torch
from PIL import Image, ImageDraw, ImageOps
from utils import combine_images, _init_input, selectRandomNodes, selectNodesTypes, get_mask_cnt
from models import Discriminator, Generator, DiscriminatorLocal, compute_gradient_penalty, weights_init, \
    compute_gradient_penalty_local

parser = argparse.ArgumentParser()
parser.add_argument("--n_epochs", type=int, default=100000, help="number of epochs of training")
parser.add_argument("--batch_size", type=int, default=1, help="size of the batches")
parser.add_argument("--g_lr", type=float, default=0.0001, help="adam: learning rate")
parser.add_argument("--d_lr", type=float, default=0.0001, help="adam: learning rate")
parser.add_argument("--b1", type=float, default=0.5, help="adam: decay of first order momentum of gradient")
parser.add_argument("--b2", type=float, default=0.999, help="adam: decay of first order momentum of gradient")
parser.add_argument("--n_cpu", type=int, default=8, help="number of cpu threads to use during batch generation")
parser.add_argument("--sample_interval", type=int, default=5000, help="interval between image sampling")
parser.add_argument("--exp_folder", type=str, default='exp', help="destination folder")
parser.add_argument("--target_set", type=int, default=8, choices=[5, 6, 7, 8], help="which split to remove")
# parser.add_argument("--data_path", type=str, default='D:\\dataset\\floorplan_json5\\', help="path to the dataset")
parser.add_argument("--data_path", type=str, default='/nfsfile/liangxiongfei/floorplan_json5/',
                    help="path to the dataset")
parser.add_argument("--lambda_gp", type=int, default=10, help="lambda for gradient penalty")
parser.add_argument("--n_critic", type=int, default=1, help="number of training steps for discriminator per iter")
opt = parser.parse_args()

localtime = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime())
exp_folder = "{}_{}".format(opt.exp_folder, localtime)
os.makedirs("/nfsfile/liangxiongfei/exps/" + exp_folder, exist_ok=True)
# os.makedirs("./exps/"+exp_folder, exist_ok=True)
checkpoint_folder = "{}".format(localtime)
# os.makedirs("./checkpoints/" + checkpoint_folder, exist_ok=True)
os.makedirs("/nfsfile/temp/liangxiongfei/checkpoints/" + checkpoint_folder, exist_ok=True)

# Loss function
adversarial_loss = torch.nn.BCEWithLogitsLoss()
distance_loss = torch.nn.L1Loss()
mask_loss = torch.nn.L1Loss()

# Initialize generator and discriminator
generator = Generator()
discriminator = Discriminator()
discriminator_local = DiscriminatorLocal()
if torch.cuda.is_available():
    device = torch.device('cuda:0')
generator.to(device)
discriminator.to(device)
discriminator_local.to(device)
adversarial_loss.to(device)
mask_loss.to(device)

generator.apply(weights_init)
discriminator.apply(weights_init)
discriminator_local.apply(weights_init)

# generator.load_state_dict(torch.load('generator.pth', map_location=device))
# discriminator.load_state_dict(torch.load('discriminator.pth', map_location=device))
# discriminator_local.load_state_dict(torch.load('discriminator_local.pth', map_location=device))




# Visualize a single batch
def visualizeSingleBatch(fp_loader_test, opt, exp_folder, batches_done, batch_size=8):
    # print('Loading saved model ... \n{}'.format('./checkpoints/{}_{}.pth'.format(exp_folder, batches_done)))
    generatorTest = Generator()
    # generatorTest.load_state_dict(torch.load('./checkpoints/{}/generator.pth'.format(checkpoint_folder)))
    generatorTest.load_state_dict(
        torch.load('/nfsfile/temp/liangxiongfei/checkpoints/{}/generator.pth'.format(checkpoint_folder)))
    generatorTest = generatorTest.eval()

    generatorTest.cuda()
    with torch.no_grad():
        # Unpack batch
        boundary, mks_test, nds_test, eds_test, nd_to_sample_test, ed_to_sample_test = next(iter(fp_loader_test))
        real_mks_test = Variable(mks_test.type(Tensor))
        given_nds_test = Variable(nds_test.type(Tensor))
        given_eds_test = eds_test
        # Select random nodes
        ind_fixed_nodes_test, _ = selectNodesTypes(nd_to_sample_test, batch_size, nds_test)
        # build input
        state_test = {'masks': real_mks_test, 'fixed_nodes': ind_fixed_nodes_test}
        graph_test = [given_nds_test, given_eds_test]
        z_test, given_masks_in_test, given_nds_test, given_eds_test = _init_input(graph_test, state_test)
        z_test, given_masks_in_test, given_nds_test, given_eds_test, real_mks_test = z_test.to(device), given_masks_in_test.to(device), \
                                                                      given_nds_test.to(device), given_eds_test.to(device), real_mks_test.to(device)
        # gen_mks = generator(z, given_masks_in, given_nds, given_eds)
        # Generate a batch of images
        generatorTest.to(device)
        gen_mks_test = generatorTest(z_test, given_masks_in_test, given_nds_test, given_eds_test)
        # Generate image tensors
        real_imgs_tensor = combine_images(real_mks_test, given_nds_test, given_eds_test, \
                                          nd_to_sample_test, ed_to_sample_test)
        fake_imgs_tensor = combine_images(gen_mks_test, given_nds_test, given_eds_test, \
                                          nd_to_sample_test, ed_to_sample_test)

        real_imgs_tensor = real_imgs_tensor[:, :3, :, :]
        fake_imgs_tensor = fake_imgs_tensor[:, :3, :, :]

        # Save images
        save_image(real_imgs_tensor, "/nfsfile/liangxiongfei/exps/{}/{}_real.png".format(exp_folder, batches_done), \
                   nrow=12, normalize=False)
        save_image(fake_imgs_tensor, "/nfsfile/liangxiongfei/exps/{}/{}_fake.png".format(exp_folder, batches_done), \
                   nrow=12, normalize=False)
        # save_image(real_imgs_tensor, "./exps/{}/{}_real.png".format(exp_folder, batches_done), \
        #            nrow=12, normalize=False)
        # save_image(fake_imgs_tensor, "./exps/{}/{}_fake.png".format(exp_folder, batches_done), \
        #            nrow=12, normalize=False)
    return


# Configure data loader
fp_dataset = FloorplanDataset(opt.data_path)
train_size = int(0.9 * len(fp_dataset))
test_size = len(fp_dataset) - train_size
fp_dataset_train, fp_dataset_test = torch.utils.data.random_split(fp_dataset, [train_size, test_size])
fp_loader = torch.utils.data.DataLoader(fp_dataset_train,
                                        batch_size=1,
                                        shuffle=False,
                                        num_workers=0,
                                        collate_fn=floorplan_collate_fn,
                                        pin_memory=False)
fp_loader_test = torch.utils.data.DataLoader(fp_dataset_test,
                                             batch_size=1,
                                             shuffle=True,
                                             num_workers=0,
                                             collate_fn=floorplan_collate_fn,
                                             pin_memory=False)
# Optimizers
optimizer_G = torch.optim.Adam(generator.parameters(), lr=opt.g_lr, betas=(opt.b1, opt.b2))
optimizer_D = torch.optim.Adam(discriminator.parameters(), lr=opt.d_lr, betas=(opt.b1, opt.b2))
optimizer_D_local = torch.optim.Adam(discriminator_local.parameters(), lr=opt.d_lr, betas=(opt.b1, opt.b2))
Tensor = torch.cuda.FloatTensor if torch.cuda.is_available() else torch.FloatTensor

# ----------
#  Training
# ----------
batches_done = 0
for epoch in range(opt.n_epochs):
    for i, batch in enumerate(fp_loader):
        # print(i)
        # print(batch)
        # Unpack batch
        boundary, mks, nds, eds, nd_to_sample, ed_to_sample = batch
        indices = nd_to_sample, ed_to_sample
        # Adversarial ground truths
        batch_size = torch.max(nd_to_sample) + 1
        n_room = nd_to_sample.size(0)
        valid = Variable(Tensor(n_room, 1) \
                         .fill_(1.0), requires_grad=False)
        mask_valid = Variable(Tensor(n_room, 1) \
                              .fill_(1.0), requires_grad=False)
        fake = Variable(Tensor(n_room, 1) \
                        .fill_(0.0), requires_grad=False)
        # Configure input
        real_mks = Variable(mks.type(Tensor))
        given_nds = Variable(nds.type(Tensor))
        given_eds = eds
        graph = [given_nds, given_eds]
        # Set grads on
        for p in discriminator.parameters():
            p.requires_grad = True
        for p in discriminator_local.parameters():
            p.requires_grad = True

        # ---------------------
        #  Train Discriminator
        # ---------------------
        optimizer_D.zero_grad()
        # Select random nodes
        ind_fixed_nodes, _ = selectNodesTypes(nd_to_sample, batch_size, nds)

        # Generate a batch of images
        state = {'masks': real_mks, 'fixed_nodes': ind_fixed_nodes}
        z, given_masks_in, given_nds, given_eds = _init_input(graph, state)
        z, given_masks_in, given_nds, given_eds, real_mks = z.to(device), given_masks_in.to(device), \
                                                            given_nds.to(device), given_eds.to(device), real_mks.to(
            device)
        gen_mks = generator(z, given_masks_in, given_nds, given_eds)

        # fake_imgs_tensor = combine_images(gen_mksz, given_masks_in, given_nds, given_eds, real_mks = z.to(device), given_masks_in.to(device), \
        #                                                   given_nds.to(device), given_eds.to(device), real_mks.to(device), given_nds, given_eds, \
        #                                   nd_to_sample, ed_to_sample)
        # save_image(fake_imgs_tensor, "./exps/{}/{}_fake.png".format(exp_folder, batches_done), \
        #            nrow=12, normalize=False)
        # real_imgs_tensor = combine_images(real_mks, given_nds, given_eds, \
        #                                   nd_to_sample, ed_to_sample)
        # save_image(real_imgs_tensor, "./exps/{}/{}_real.png".format(exp_folder, batches_done), \
        #            nrow=12, normalize=False)
        #
        #
        # Real images
        real_validity = discriminator(real_mks, given_nds, given_eds, nd_to_sample)
        # Fake images
        fake_validity = discriminator(gen_mks.detach(), given_nds.detach(), \
                                      given_eds.detach(), nd_to_sample.detach())
        # Measure discriminator's ability to classify real from generated samples
        gradient_penalty = compute_gradient_penalty(discriminator, real_mks.data, \
                                                    gen_mks.data, given_nds.data, \
                                                    given_eds.data, nd_to_sample.data, \
                                                    None)

        d_loss = -torch.mean(real_validity) + torch.mean(fake_validity) \
                 + opt.lambda_gp * gradient_penalty
        # Update discriminator
        d_loss.backward()
        optimizer_D.step()

        optimizer_D_local.zero_grad()
        real_validity_local = discriminator_local(real_mks, given_nds, nd_to_sample)
        fake_validity_local = discriminator_local(gen_mks.detach(), given_nds.detach(), nd_to_sample.detach())
        gradient_penalty_local = compute_gradient_penalty_local(discriminator_local, real_mks.data, \
                                                    gen_mks.data, given_nds.data, \
                                                    given_eds.data, nd_to_sample.data, \
                                                    None)
        d_local_loss = -torch.mean(real_validity_local) + torch.mean(fake_validity_local) + opt.lambda_gp * gradient_penalty_local
        d_local_loss.backward()
        optimizer_D_local.step()

        # -----------------
        #  Train Generator
        # -----------------
        optimizer_G.zero_grad()
        # Set grads off
        for p in discriminator.parameters():
            p.requires_grad = False
        for p in discriminator_local.parameters():
            p.requires_grad = False
        # Train the generator every n_critic steps
        if i % opt.n_critic == 0:
            # Generate a batch of images

            z = Variable(Tensor(np.random.normal(0, 1, tuple((real_mks.shape[0], 128)))))
            z, given_masks_in, given_nds, given_eds, real_mks = z.to(device), given_masks_in.to(device), \
                                                                given_nds.to(device), given_eds.to(device), real_mks.to(device)
            gen_mks = generator(z, given_masks_in, given_nds, given_eds)
            # Score fake images
            fake_validity = discriminator(gen_mks, given_nds, given_eds, nd_to_sample)
            fake_validity_local = discriminator_local(gen_mks, given_nds, nd_to_sample)
            # Compute L1 loss
            err = distance_loss(gen_mks[ind_fixed_nodes, :, :], given_masks_in[ind_fixed_nodes, 0, :, :]) * 1000 \
                if len(ind_fixed_nodes) > 0 else torch.tensor(0.0)
            # Update generator
            # g_ad_loss = adversarial_loss(fake_validity_local, valid)
            # g_ad_loss = -torch.mean(fake_validity_local)
            mask_cnt = get_mask_cnt(gen_mks.detach().cpu())
            #
            # # g_loss = -torch.mean(fake_validity) + err + 5 * g_ad_loss
            mask_cnt = mask_cnt.to(device)
            mask_valid = mask_valid.to(device)
            err2 = mask_loss(mask_cnt, mask_valid)
            g_loss = -torch.mean(fake_validity) - torch.mean(fake_validity_local) + err + err2*10000
            g_loss.backward()
            # Update optimizer
            optimizer_G.step()
            print("[Epoch %d/%d] [Batch %d/%d] [D loss: %f] [D local loss: %f][G loss: %f] [L1 loss: %f] [Mask Loss: %f]"
                  % (epoch, opt.n_epochs, i, len(fp_loader), d_loss.item(), d_local_loss.item(), g_loss.item(), err.item(), err2.item()))
            if (batches_done % opt.sample_interval == 0):
                # torch.save(generator.state_dict(), './checkpoints/{}/generator.pth'.format(checkpoint_folder))
                # torch.save(discriminator.state_dict(), './checkpoints/{}/discriminator.pth'.format(checkpoint_folder))
                # torch.save(discriminator_local.state_dict(), './checkpoints/{}/discriminator_local.pth'.format(checkpoint_folder))
                torch.save(generator.state_dict(),
                           '/nfsfile/temp/liangxiongfei/checkpoints/{}/generator.pth'.format(checkpoint_folder))
                torch.save(discriminator.state_dict(),
                           '/nfsfile/temp/liangxiongfei/checkpoints/{}/discriminator.pth'.format(checkpoint_folder))
                torch.save(discriminator_local.state_dict(), '/nfsfile/temp/liangxiongfei/checkpoints/{}/discriminator_local.pth'.format(checkpoint_folder))
                visualizeSingleBatch(fp_loader_test, opt, exp_folder, batches_done)
            batches_done += opt.n_critic
