from models import Generator, AutoEncoder
import torch
import numpy as np
from utils import _init_input, ID_COLOR, draw_masks, draw_graph, estimate_graph, get_mask_cnt, beautify_room, \
    rectangle_room, is_overlap, is_neighbor, save_image

class FloorplanGAN:
    def __init__(self, num, room_types, edges):
        z = torch.randn(num, 128).float()
        nodes = torch.eye(18)[room_types, :]
        mask = torch.zeros(num, 2, 64, 64)
        generator = Generator()
        autoencoder = AutoEncoder()
        generator.load_state_dict(torch.load('generator.pth'), map_location=torch.device('cuda:0'))
        generator.eval()
        autoencoder.load_state_dict(torch.load('autoencoder.pth'), map_location=torch.device('cuda:0'))
        autoencoder.eval()
        device = torch.device('cuda:0')
        Tensor = torch.cuda.FloatTensor

        node_to_sample, edge_to_sample = torch.zeros(num, 1), torch.zeros(num, 1)
        z, nodes, mask, edges = z.to(device), nodes.to(device), mask.to(device), edges.to(device)
        node_to_sample, edge_to_sample = node_to_sample.to(device), edge_to_sample.to(device)

    def infer_masks(self, real_masks, nds, eds):
        masks = torch.zeros((len(real_masks), 2, 64, 64))
        # masks[:, 1, :, :] = torch.ones((64, 64))
        z = torch.randn(len(masks), 128).float()
        room_type = torch.where(nds > 0)[1]
        masks[:, 0, :, :] = -torch.ones((64, 64))
        parlor_idx = torch.where(room_type == 1)

        while True:
            gen_masks = self.generator(z.to('cuda'), masks.to('cuda'), nds.to('cuda'), eds.to('cuda'))
            mask_cnt = get_mask_cnt(gen_masks.detach().cpu())
            if mask_cnt[parlor_idx] == 1:
                break
        # im0 = draw_masks(gen_masks[parlor_idx].detach().cpu().numpy().copy(), nds)
        # im0 = torch.tensor(np.array(im0).transpose((2, 0, 1)))/255.0
        # save_image(im0, './{}/fp_{}.png'.format(opt.out, 0), nrow=1, normalize=False) # visualize init image

        for parlor_index in parlor_idx:
            masks[parlor_index.item(), 0] = beautify_room(gen_masks[parlor_idx][0])
            masks[parlor_index.item(), 1] = torch.ones((64, 64))

        # im0 = draw_masks(masks[:,0].detach().cpu().numpy().copy(), nds)
        # im0 = torch.tensor(np.array(im0).transpose((2, 0, 1)))/255.0
        # save_image(im0, './{}/fp_{}.png'.format(opt.out, 1), nrow=1, normalize=False) # visualize init image
        room_idx = torch.where(room_type < 15)[0]
        door_idx = torch.where(room_type >= 15)[0]
        # room_idx = torch.where(room_idx!=1)
        idx = [parlor_idx[0].item()]
        for i in range(100):
            z = torch.randn(len(masks), 128).float()
            gen_masks = self.generator(z.to('cuda'), masks.to('cuda'), nds.to('cuda'), eds.to('cuda'))
            mask_cnt = get_mask_cnt(gen_masks.detach().cpu())
            check = True

            for room_index in room_idx:
                if room_index in idx:
                    continue
                if mask_cnt[room_index] == 1:
                    gen_masks[room_index] = rectangle_room(gen_masks[room_index])
                    if not is_overlap(masks, idx, gen_masks[room_index]):
                        masks[room_index.item(), 0] = gen_masks[room_index]
                        masks[room_index.item(), 1] = torch.ones((64, 64))
                        idx.append(room_index.item())
                else:
                    check = False
            if len(idx) == len(room_idx) and check:
                break

        im0 = draw_masks(masks[:, 0, :, :].detach().cpu().numpy().copy(), nds)
        im0 = torch.tensor(np.array(im0).transpose((2, 0, 1))) / 255.0

        gen_masks = self.generator(z.to('cuda'), masks.to('cuda'), nds.to('cuda'), eds.to('cuda'))



        im0 = draw_masks(gen_masks.detach().cpu().numpy().copy(), nds)
        im0 = torch.tensor(np.array(im0).transpose((2, 0, 1))) / 255.0
        save_image(im0, 'result.png'.format(1, 1), nrow=1, normalize=False)  # visualize init image

    def design(self):
        gen_mask = self.infer_masks(self.mask, self.nodes, self.edges)
        gen_mask = self.autoencoder(gen_mask)
        save_image(gen_mask, 'result.png'.format(1, 1), nrow=1, normalize=False)  # visualize init image








