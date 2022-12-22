import cv2
import numpy as np
import json
import torch
import random
from PIL import Image, ImageDraw
import webcolors
from torch.autograd import Variable
import random

ID_COLOR = {0: '#FFB6C1', 1: '#EE4D4D', 2: '#C67C7B', 3: '#FFD274', 4: '#BEBEBE', 5: '#BFE3E8', 6: '#7BA779',
            7: '#E87A90', 8: '#FF8C69', 9: '#1E90FF', 10: '#1F849B', 11: '#7FFFAA', 12: '#ADFF2F', 13: '#FFFF00',
            14: '#FFD700', 15: '#727171', 16: '#785A67', 17: '#D3A2C7'}


def mask2polygon(mask):
    contours, hierarchy = cv2.findContours((mask).astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # mask_new, contours, hierarchy = cv2.findContours((mask).astype(np.uint8), cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    segmentation = []
    for contour in contours:
        contour_list = contour.flatten().tolist()
        if len(contour_list) > 4:  # and cv2.contourArea(contour)>10000
            segmentation.append(contour_list)
    return segmentation


def polygon_format(polygons, mask):
    for i in range(len(polygons)):
        polygon = polygons[i]
        new_polygon = []
        if len(polygon) > 0:
            new_polygon.append([polygon[0], polygon[1]])
        for j in range(1, len(polygon) // 2):
            point_pre = [new_polygon[-1][0], new_polygon[-1][1]]
            point_cur = [polygon[2 * j], polygon[2 * j + 1]]
            if abs(point_pre[0] - point_cur[0]) == 1 and abs(point_pre[1] - point_cur[1]) == 1:
                if mask[point_pre[1]][point_cur[0]] != 0:
                    new_polygon.pop()
                    new_polygon.append([point_cur[0], point_pre[1]])
                elif mask[point_cur[1]][point_pre[0]] != 0:
                    new_polygon.pop()
                    new_polygon.append([point_pre[0], point_cur[1]])
                else:
                    new_polygon.append(point_cur)
            else:
                new_polygon.append(point_cur)
        polygons[i] = new_polygon
    return polygons


def read_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data['boundary'], data['room_type'], data['room_polygons'], data['room_bbox'], data['doors'], data['edges']


def colider2D(polygon1, room_mask):
    x1, y1 = polygon1[0]
    x2, y2 = polygon1[2]
    for i in range(x1, x2 + 1):
        for j in range(y1, y2 + 1):
            if room_mask[j][i] == 1:
                return True
    return False


def polygon_format2(polygon, mask):
    for i in range(1, len(polygon)):
        p1 = polygon[i - 1]
        p2 = polygon[i]
        if p1[0] == p2[0]:
            miny = min(p1[1], p2[1])
            maxy = max(p1[1], p2[1])
            for j in range(miny, maxy + 1):
                mask[p1[0]][j] = 1
        elif p1[1] == p2[1]:
            minx = min(p1[0], p2[0])
            maxx = max(p1[0], p2[0])
            for j in range(minx, maxx + 1):
                mask[j][p1[1]] = 1
    return mask


def selectNodesType(nds_tp_sample, batch_size, nds):
    all_types = list(range(18))
    shift = 0
    fixed_nodes = []
    for i in range(batch_size):
        rooms = np.where(nds_tp_sample == i)
        rooms_num = len(rooms[0])
        room_type = np.where(nds[rooms] == 1)[1]
        selected_type = [t for t in all_types if random.uniform(0, 1) > 0.5]
        fixed_rooms = [r for r, r_type in enumerate(room_type) if r_type in selected_type]
        fixed_rooms = torch.tensor(fixed_rooms).cuda()
        fixed_rooms += shift
        fixed_nodes.append(fixed_rooms)
        shift += rooms_num
    fixed_nodes = torch.cat(fixed_nodes)
    fixed_nodes = fixed_nodes.long()
    return fixed_nodes


def fix_nodes(prev_masks, fixed_nodes):
    given_masks = prev_masks.clone().detach()
    not_fixed_nodes = torch.tensor([k for k in range(given_masks.shape[0]) if k not in fixed_nodes])
    given_masks[not_fixed_nodes.long()] = -1.0
    given_masks = given_masks.unsqueeze(1)

    inds_mask = torch.zeros_like(given_masks)
    inds_mask[not_fixed_nodes.long()] = 0.0
    inds_mask[fixed_nodes.long()] = 1.0
    given_masks = torch.cat([given_masks, inds_mask], 1)
    return given_masks


def random_mask(room_masks):
    rm_mks = room_masks.clone()
    for i in range(len(room_masks)):
        if random.random() < 0.5:
            rm_mks[i] = torch.zeros((64, 64))
    return rm_mks


def init_input(graph, state=None, mask_size=256):
    given_nds, given_eds = graph
    given_nds = given_nds.float()
    given_eds = given_eds.clone().detach().long()
    z = torch.randn(len(given_nds), 128).float()

    fixed_nodes = state['fixed_nodes']
    prev_mask = torch.zeros((given_nds.shape[0], mask_size, mask_size)) - 1.0 if (state['mask'] is None) else state[
        'mask']
    given_mask = fix_nodes(prev_mask, fixed_nodes.clone().detach())
    return z, given_mask, given_nds, given_eds


def image_resize(image, size):
    image = Image.fromarray(image)
    return np.array(image.resize(size))


def resize_boundary(boundary_mask, node_to_sample):
    batch_size = torch.max(node_to_sample) + 1
    new_boundary_mask = []
    for i in range(batch_size):
        rooms = np.where(node_to_sample == i)
        room_num = len(rooms[0])
        mask = np.expand_dims(boundary_mask[i].cpu().numpy(), 0).repeat(room_num, axis=0)
        new_boundary_mask.append(torch.tensor(mask))
    new_boundary_mask = torch.cat(new_boundary_mask)
    return new_boundary_mask


def draw_masks(masks, real_nodes, im_size=256):
    bg_img = Image.new("RGBA", (im_size, im_size), (255, 255, 255, 255))  # Semitransparent background.
    for m, nd in zip(masks, real_nodes):
        # resize map
        m[m > 0] = 255
        m[m < 0] = 0
        m_lg = cv2.resize(m, (im_size, im_size), interpolation=cv2.INTER_AREA)
        nd = np.where(nd > 0)[0][0]
        # pick color
        color = ID_COLOR[nd]
        r, g, b = webcolors.hex_to_rgb(color)

        # set drawer
        dr_bkg = ImageDraw.Draw(bg_img)

        # draw region
        m_pil = Image.fromarray(m_lg)
        dr_bkg.bitmap((0, 0), m_pil.convert('L'), fill=(r, g, b, 256))

        # draw contour
        m_cv = m_lg[:, :, np.newaxis].astype('uint8')
        ret, thresh = cv2.threshold(m_cv, 127, 255, 0)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if len(contours) > 0]
        cnt = np.zeros((256, 256, 3)).astype('uint8')
        cv2.drawContours(cnt, contours, -1, (255, 255, 255, 255), 1)
        cnt = Image.fromarray(cnt)
        dr_bkg.bitmap((0, 0), cnt.convert('L'), fill=(0, 0, 0, 255))

    return bg_img.resize((im_size, im_size))


def combine_images(samples_batch, nodes_batch, edges_batch, nd_to_sample, ed_to_sample):
    samples_batch = samples_batch.detach().cpu().numpy()
    nodes_batch = nodes_batch.detach().cpu().numpy()
    edges_batch = edges_batch.detach().cpu().numpy()
    batch_size = torch.max(nd_to_sample) + 1
    all_imgs = []
    shift = 0
    for b in range(batch_size):
        # split batch
        inds_nd = np.where(nd_to_sample == b)
        inds_ed = np.where(ed_to_sample == b)
        sps = samples_batch[inds_nd]
        nds = nodes_batch[inds_nd]
        eds = edges_batch[inds_ed]

        # draw
        # graph_image = draw_graph_with_types(nds, eds, shift)
        _image = draw_masks(sps, nds)

        # store
        # all_imgs.append(torch.FloatTensor(np.array(graph_image.convert('RGBA')).\
        #                              astype('float').\
        #                              transpose(2, 0, 1))/255.0)
        all_imgs.append(torch.FloatTensor(np.array(_image.convert('RGBA')). \
                                          astype('float'). \
                                          transpose(2, 0, 1)) / 255.0)
        shift += len(nds)
    return torch.stack(all_imgs)


def get_bbox_center(polygon):
    polygon = np.array(polygon)
    min_x, min_y = np.amin(polygon, axis=0)
    max_x, max_y = np.amax(polygon, axis=0)
    return [min_x, min_y, max_x, max_y], np.mean(polygon, axis=0)


def get_relative_position(point, bbox):
    point_x, point_y = point
    min_x, min_y, max_x, max_y = bbox
    if point_x <= min_x and point_y <= min_y:  # left-above
        return 2
    elif min_x < point_x < max_x and point_y <= min_y:  # above
        return 3
    elif point_x >= max_x and point_y <= min_y:  # right-above
        return 4
    elif point_x <= min_x and min_y < point_y < max_y:  # left
        return 5
    elif min_x < point_x < max_x and min_y < point_y < max_y:  # inside
        return 6
    elif point_x >= max_x and min_y < point_y < max_y:  # right
        return 7
    elif point_x <= min_x and point_y >= max_y:  # left-blow
        return 8
    elif min_x < point_x < max_x and point_y >= max_y:  # blow
        return 9
    elif point_x >= max_x and point_y >= max_y:  # right-blow
        return 10


def inflate_mask(mask):
    x = []
    y = []
    for i in range(1, 63):
        for j in range(1, 63):
            if mask[i][j] < 0 and (
                    mask[i - 1][j - 1] > 0 or mask[i - 1][j] > 0 or mask[i][j - 1] > 0 or mask[i - 1][j + 1] > 0 or
                    mask[i][j + 1] > 0 or mask[i + 1][j] > 0 or mask[i + 1][j + 1] > 0 or mask[i + 1][j - 1] > 0):
                x.append(i)
                y.append(j)
    for i in range(len(x)):
        mask[x[i]][y[i]] = 1
    return mask


def update_edgeType(room_polygons, room_type, edge):
    for i in range(edge.shape[0]):
        for j in range(i + 1, edge.shape[1]):
            if edge[i][j] > 0:
                if room_type[i] == 15 or room_type[i] == 17 or room_type[j] == 15 or room_type[j] == 17:
                    edge[i][j] = 1
                    edge[j][i] = 1
                else:
                    rm_polygon1 = room_polygons[i]
                    rm_polygon2 = room_polygons[j]
                    rm_bbox1, rm_center1 = get_bbox_center(rm_polygon1)
                    rm_bbox2, rm_center2 = get_bbox_center(rm_polygon2)
                    position = get_relative_position(rm_center1, rm_bbox2)
                    if position != 6:
                        edge[i][j] = position
                        edge[j][i] = 12 - position
                    else:
                        position = get_relative_position(rm_center2, rm_bbox1)
                        if position != 6:
                            edge[j][i] = position
                            edge[i][j] = 12 - position
                        elif rm_center1[0] - rm_center2[0] < -5 and rm_center1[1] - rm_center2[1] < -5:
                            edge[i][j] = 2
                            edge[j][i] = 10
                        elif abs(rm_center1[0] - rm_center2[0]) < 5 and rm_center1[1] - rm_center2[1] < -5:
                            edge[i][j] = 3
                            edge[i][j] = 9
                        elif rm_center1[0] - rm_center2[0] > 5 and rm_center1[1] - rm_center2[1] < -5:
                            edge[i][j] = 4
                            edge[i][j] = 8
                        elif rm_center1[0] - rm_center2[0] < -5 and abs(rm_center1[1] - rm_center2[1]) < 5:
                            edge[i][j] = 5
                            edge[j][i] = 7
                        elif abs(rm_center1[0] - rm_center2[0]) < 5 and abs(rm_center1[1] - rm_center2[1]) < 5:
                            edge[i][j] = 6
                            edge[i][j] = 6
                        elif rm_center1[0] - rm_center2[0] > 5 and abs(rm_center1[1] - rm_center2[1]) < 5:
                            edge[i][j] = 7
                            edge[i][j] = 5
                        elif rm_center1[0] - rm_center2[0] < -5 and rm_center1[1] - rm_center2[1] > 5:
                            edge[i][j] = 8
                            edge[j][i] = 4
                        elif abs(rm_center1[0] - rm_center2[0]) < 5 and rm_center1[1] - rm_center2[1] > 5:
                            edge[i][j] = 9
                            edge[i][j] = 3
                        elif rm_center1[0] - rm_center2[0] > 5 and rm_center1[1] - rm_center2[1] > 5:
                            edge[i][j] = 10
                            edge[i][j] = 2
    new_edge = []
    for i in range(edge.shape[0]):
        for j in range(edge.shape[1]):
            if edge[i][j] > 0:
                new_edge.append([i, edge[i][j], j])
            else:
                new_edge.append([i, -1, j])
    return new_edge


def salt_and_pepper(X, prop):
    X_clone = X.clone().view(-1, 1)
    num_feature = X_clone.size(0)
    mn = X_clone.min()
    mx = X_clone.max()
    indices = np.random.randint(0, num_feature, int(num_feature * prop))
    for elem in indices:
        if np.random.random() < 0.5:
            X_clone[elem] = mn
        else:
            X_clone[elem] = mx
    return X_clone.view(X.size())


def masking(X, p):
    X_clone = X.clone()
    lenx = X_clone.size(2)
    leny = X_clone.size(3)
    for i in range(X_clone.size(0)):
        maskx = np.random.uniform(p, 1, 1)
        masky = p / maskx
        maskx = int(maskx * lenx)
        masky = int(masky * leny)
        idx = np.random.randint(0, lenx - maskx, 1)[0]
        idy = np.random.randint(0, leny - masky, 1)[0]
        for j in range(idx, idx + maskx):
            for k in range(idy, idy + masky):
                X_clone[i][0][j][k] = 0
    return X_clone.view(X.size())


def cut_image(image):
    image = image.reshape((256, 256))
    block = []
    for i in range(16):
        for j in range(16):
            block.append(image[16 * i:16 * i + 16, 16 * j:16 * j + 16].detach().cpu().numpy())
    block = np.array(block)
    block = torch.cuda.FloatTensor(block)
    block = block.to(image.device)
    return block


class ReplayBuffer:
    def __init__(self, max_size=50):
        assert max_size > 0, "Empty buffer or trying to create a black hole. Be careful."
        self.max_size = max_size
        self.data = []

    def push_and_pop(self, data):
        to_return = []
        for element in data.data:
            element = torch.unsqueeze(element, 0)
            if len(self.data) < self.max_size:
                self.data.append(element)
                to_return.append(element)
            else:
                if random.uniform(0, 1) > 0.5:
                    i = random.randint(0, self.max_size - 1)
                    to_return.append(self.data[i].clone())
                    self.data[i] = element
                else:
                    to_return.append(element)
        return Variable(torch.cat(to_return))


class LambdaLR:
    def __init__(self, n_epochs, offset, decay_start_epoch):
        assert (n_epochs - decay_start_epoch) > 0, "Decay must start before the training session ends!"
        self.n_epochs = n_epochs
        self.offset = offset
        self.decay_start_epoch = decay_start_epoch

    def step(self, epoch):
        return 1.0 - max(0, epoch + self.offset - self.decay_start_epoch) / (self.n_epochs - self.decay_start_epoch)
