import os
import torch
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
from torch.utils.data import Dataset
from utils2 import read_json, polygon_format2, image_resize, update_edgeType
from utils import get_mask_cnt
from skimage.draw import polygon2mask
from tqdm import tqdm

class FloorplanDataset(Dataset):
    def __init__(self, path):
        self.path = path
        files = os.listdir(self.path)
        self.graphs = []
        for file in tqdm(files):
            graph = []
            boundary, room_type, room_polygons, room_bbox, doors, edges = read_json(self.path + file)
            graph.append(boundary)
            graph.append(room_type)
            graph.append(room_polygons)
            graph.append(room_bbox)
            graph.append(doors)
            graph.append(edges)
            self.graphs.append(graph)

    def __len__(self):
        return len(os.listdir(self.path))

    def __getitem__(self, index):
        graph = self.graphs[index]
        boundary = graph[0].copy()
        room_types = graph[1].copy()
        room_polygons = graph[2].copy()
        doors = graph[4].copy()
        edges = graph[5].copy()
        room_number, door_number = len(room_types), len(doors)
        room_types.extend([17] * (len(doors) - 1))
        room_types.append(15)
        out_door = doors[0].copy()
        del(doors[0])
        doors.append(out_door)
        for i in range(0, len(doors)):
            door_polygon = [[doors[i][0][0]-2, doors[i][0][1]-2], [doors[i][0][0]-2, doors[i][1][1]+2],
                            [doors[i][1][0]+2, doors[i][1][1]+2], [doors[i][1][0]+2, doors[i][0][1]-2]]
            room_polygons.append(door_polygon)
        new_edge = np.zeros((room_number + door_number, room_number + door_number), dtype=np.int32)
        for i in range(room_number+1):
            for j in range(i+1, room_number+1):
                if edges[i][j] > 1:
                    door_no = edges[i][j]
                    new_edge[i][int(door_no + room_number - 2)] = 1
                    new_edge[int(door_no + room_number - 2)][i] = 1
                    new_edge[j][int(door_no + room_number - 2)] = 1
                    new_edge[int(door_no + room_number - 2)][j] = 1
                    # new_edge[i][j] = 1
                    # new_edge[j][i] = 1
                elif edges[i][j] == 1:
                    new_edge[i][room_number+door_number-1] = 1
                    new_edge[room_number+door_number-1][i] = 1

        room_masks = []
        for i, polygon in enumerate(room_polygons):
            polygon.append(polygon[0])
            polygon = np.array(polygon)
            polygon = polygon[:, [1, 0]]
            mask = polygon2mask((256, 256), polygon)
            mask = np.array(mask, dtype=np.int32)
            mask = polygon_format2(polygon, mask)

            mask = image_resize(mask, (64, 64))
            mask[mask <= 0] = -1
            room_masks.append(mask)

        # for i in range(len(room_types)):
        #     room_types[i] = room_types[i] - 1
        # room_masks = np.array(room_masks)
        rm_types = torch.eye(18)[room_types, :]
        boundary_mask = polygon2mask((256, 256), boundary)
        boundary_mask = np.array(boundary_mask, dtype=np.int32)
        boundary_mask = polygon_format2(boundary, boundary_mask)
        boundary_mask = np.transpose(boundary_mask)
        # plt.imshow(boundary_mask)
        # plt.show()
        # boundary_mask = boundary_mask + 2 * room_masks[-1]
        boundary_mask = image_resize(boundary_mask, (64, 64))
        # plt.imshow(boundary_mask)
        # plt.show()

        edge = []
        for i in range(len(new_edge)):
            for j in range(i+1, len(new_edge)):
                if new_edge[i][j] > 0:
                    edge.append([i, 1, j])
                else:
                    edge.append([i, -1, j])
                    # door = room_polygons[j]
                    # rm_mk = room_masks[i]
                    # x = abs(door[2][0] - door[0][0])
                    # y = abs(door[2][1] - door[0][1])
                    # if x > y:
                    #     if rm_mk[door[0][1]-1][(door[0][0]+door[2][0])//2] == 1:
                    #         edge.append([i, 0, j])  # up
                    #     elif rm_mk[door[2][1]+1][(door[0][0]+door[2][0])//2] == 1:
                    #         edge.append([i, 1, j])  # down
                    #     else:
                    #         print('Error')
                    # else:
                    #     if rm_mk[(door[0][1]+door[2][1])//2][door[0][0]-1] == 1:
                    #         edge.append([i, 2, j])  # left
                    #     elif rm_mk[(door[0][1]+door[2][1])//2][door[2][0]+1] == 1:
                    #         edge.append([i, 3, j])
                    #     else:
                    #         print('Error')

        for i in range(len(room_masks)):
            room_masks[i] = image_resize(room_masks[i], (64, 64))
        room_masks = np.array(room_masks)
        boundary_mask = boundary_mask + 2 * room_masks[-1]

        return boundary_mask, room_masks, rm_types, edge


def floorplan_collate_fn(batch):
    all_room_masks, all_nodes, all_edges = [], [], []
    all_node_to_sample, all_edge_to_sample = [], []
    node_offset = 0
    all_boundary_masks = []
    for i, (boundary_mask, room_masks, nodes, edges) in enumerate(batch):
        room_masks = torch.from_numpy(room_masks)
        boundary_mask = torch.from_numpy(boundary_mask)
        boundary_mask = boundary_mask.reshape(-1, 64, 64)
        # nodes = torch.LongTensor(nodes)
        edges = torch.LongTensor(edges)
        O, T = nodes.size(0), edges.size(0)
        all_room_masks.append(room_masks)
        all_boundary_masks.append(boundary_mask)
        all_nodes.append(nodes)

        edges = edges.clone()
        if edges.shape[0] > 0:
            edges[:, 0] += node_offset
            edges[:, 2] += node_offset
            all_edges.append(edges)
        all_node_to_sample.append(torch.LongTensor(O).fill_(i))
        all_edge_to_sample.append(torch.LongTensor(T).fill_(i))
        node_offset += O
    all_room_masks = torch.cat(all_room_masks, 0)
    all_boundary_masks = torch.cat(all_boundary_masks, 0)
    all_nodes = torch.cat(all_nodes)
    if len(all_edges) > 0:
        all_edges = torch.cat(all_edges)
    else:
        all_edges = torch.tensor([])
    all_node_to_sample = torch.cat(all_node_to_sample)
    all_edge_to_sample = torch.cat(all_edge_to_sample)

    return all_boundary_masks, all_room_masks, all_nodes, all_edges, all_node_to_sample, all_edge_to_sample

