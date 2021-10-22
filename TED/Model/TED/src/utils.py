import gc
import random
import numpy as np
from collections import defaultdict
import torch.nn.functional as F

import torch


def convert(posi, nega, posi_size, nega_size, batch_size):
    
    posi = posi[np.random.randint(posi_size, size=batch_size), :]
    nega = nega[np.random.randint(nega_size, size=batch_size), :]
    
    seeds = set()
    for each in posi.flatten():
        seeds.add(each)
    for each in nega.flatten():
        seeds.add(each)
    seeds = np.sort(list(seeds))
    
    index_dict = {k:v for v,k in enumerate(seeds)}
    indices = np.array([index_dict[k] for k in seeds])
    
    new_posi, new_nega = [], []
    for (pleft, pright), (nleft, nright) in zip(posi, nega):
        new_posi.append([index_dict[pleft], index_dict[pright]])
        new_nega.append([index_dict[nleft], index_dict[nright]])
    
    return seeds, indices, np.array(new_posi), np.array(new_nega)
        

def set_seed(seed, device):
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if device=="cuda":
        torch.cuda.manual_seed(seed)


def sample(target_pool, positive_edges):
    
    positive_pool = set()
    for edge in positive_edges:
        positive_pool.add(tuple(sorted(edge)))
        
    negative_edges = set()
    positive_count, negative_count = positive_edges.shape[0], 0
    while negative_count < positive_count:
        nega_left, nega_right = np.random.choice(list(target_pool), size=positive_count-int(negative_count/2), replace=True), np.random.choice(list(target_pool), size=positive_count-int(negative_count/2), replace=True)
        for each_left, each_right in zip(nega_left, nega_right):
            if each_left==each_right: continue
            if tuple(sorted([each_left, each_right])) in positive_pool: continue
            if (each_left, each_right) in negative_edges: continue
            negative_edges.add((each_left, each_right))
            negative_count += 1
            if negative_count >= positive_count: break
                
    negative_edges = np.array(list(negative_edges)).astype(np.int32)
    return negative_edges    


def load_label(label_path, id_name):
    
    name_id, id_label, all_labels = {v:k for k,v in id_name.items()}, {}, set()
    train_set, multi = set(), False
    with open(label_path, 'r') as file:
        for line in file:
            node, label = line[:-1].split('\t')
            train_set.add(name_id[int(node)])    
            if multi or ',' in label:
                multi = True
                label_array = np.array(label.split(',')).astype(int)
                for each in label_array:
                    all_labels.add(each)
                id_label[name_id[int(node)]] = label_array
            else:
                all_labels.add(int(label))
                id_label[name_id[int(node)]] = int(label)
    train_pool = np.sort(list(train_set))
    
    train_label = []
    for k in train_pool:
        if multi:
            curr_label = np.zeros(len(all_labels)).astype(int)
            curr_label[id_label[k]] = 1
            train_label.append(curr_label)
        else:
            train_label.append(id_label[k])
    train_label = np.array(train_label)

    return train_pool, train_label, len(all_labels), multi


def load_data_semisupervised(args, node, edge, config, rpt, meta):
    
    print('check 0', flush=True)
    lines = open(config, 'r').readlines()
    target, useful_types = int(lines[0][:-1]), set()
    for each in lines[2].split('\t'):
        start, end, ltype = each.split(',')
        start, end, ltype = int(start), int(end), int(ltype)
        if ltype in meta:
            useful_types.add(ltype)
    print('check 1', flush=True)
    id_inc, id_name, name_id, name_attr = 0, {}, {}, {}
    id_inc_item, id_name_item, name_id_item, item_attr = 0, {}, {}, {}
    id_inc_person, id_name_person, name_id_person, person_attr = 0, {}, {}, {}
    with open(node, 'r') as file: 
        for line in file:
            if args.attributed=='True': nid, ntype, attr = line[:-1].split('\t')
            elif args.attributed=='False': nid, ntype = line[:-1].split('\t')
            nid, ntype = int(nid), int(ntype)
            if ntype == target:                
                name_id[nid] = id_inc
                id_name[id_inc] = nid
                if args.attributed=='True': name_attr[nid] = np.array(attr.split(',')).astype(np.float32)
                id_inc += 1
            elif ntype == 2:
                name_id_item[nid] = id_inc_item
                id_name_item[id_inc_item] = nid
                if args.attributed=='True': item_attr[nid] = np.array(attr.split(',')).astype(np.float32)
                id_inc_item += 1
            elif ntype == 3:
                name_id_person[nid] = id_inc_person
                id_name_person[id_inc_person] = nid
                if args.attributed=='True': person_attr[nid] = np.array(attr.split(',')).astype(np.float32)
                id_inc_person += 1
                
    print('check 2', flush=True)
    type_corners = {ltype:defaultdict(set) for ltype in useful_types}
    with open(edge, 'r') as file:
        for line in file:
            start, end, ltype = line[:-1].split('\t')
            start, end, ltype = int(start), int(end), int(ltype)

            if ltype in useful_types:
                if start in name_id:
                    type_corners[ltype][end].add(name_id[start])
                if end in name_id:
                    type_corners[ltype][start].add(name_id[end])
    
    print('check 3', flush=True)            
    adjs = []
    pattern = rpt + meta
    for patt in pattern:
        if patt == 'PCC':
            pattern_neighbor = defaultdict(set)
            with open('./data/T20H/pattern/{}.dat'.format(patt), 'r') as file:
                for j, line in enumerate(file):
                    id = line[:-1].split('\t')
                    if j != 0 and int(id[1]) in name_id and int(id[2]) in name_id:
                        if name_id[int(id[1])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[1])]] = [[name_id_person[int(id[0])], name_id[int(id[2])]]]
                        else:
                            pattern_neighbor[name_id[int(id[1])]].append([name_id_person[int(id[0])], name_id[int(id[2])]])

                        if name_id[int(id[2])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[2])]] = [[name_id_person[int(id[0])], name_id[int(id[1])]]]
                        else:
                            pattern_neighbor[name_id[int(id[2])]].append([name_id_person[int(id[0])], name_id[int(id[1])]])
                        
            for t in pattern_neighbor:
                pattern_neighbor[t] = list(set([tuple(l) for l in pattern_neighbor[t]]))
            print('check 3.1', flush=True)
            rights, counts = [], np.zeros(id_inc).astype(int)
            all = 0
            for i in range(id_inc):
                if i in pattern_neighbor:
                    for pattern_instance in pattern_neighbor[i]:
                        rights.append(pattern_instance)
                    counts[i] = len(pattern_neighbor[i])
                    all = all + len(pattern_neighbor[i])
            adjs.append((np.concatenate(rights), counts))
            print('check 3.2', flush=True)
            del rights, counts
            gc.collect()
            print('check 3.3', flush=True)
        elif patt == 'PCCC':
            pattern_neighbor = defaultdict(set)
            with open('./data/T20H/pattern/{}.dat'.format(patt), 'r') as file:
                for j, line in enumerate(file):
                    id = line[:-1].split('\t')
                    if j != 0 and int(id[1]) in name_id and int(id[2]) in name_id and int(id[3]) in name_id:
                        if name_id[int(id[1])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[1])]] = [[name_id_person[int(id[0])], name_id[int(id[2])], name_id[int(id[3])]]]
                        else:
                            pattern_neighbor[name_id[int(id[1])]].append([name_id_person[int(id[0])], name_id[int(id[2])], name_id[int(id[3])]])

                        if name_id[int(id[2])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[2])]] = [[name_id_person[int(id[0])], name_id[int(id[1])], name_id[int(id[3])]]]
                        else:
                            pattern_neighbor[name_id[int(id[2])]].append([name_id_person[int(id[0])], name_id[int(id[1])], name_id[int(id[3])]])

                        if name_id[int(id[3])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[3])]] = [[name_id_person[int(id[0])], name_id[int(id[1])], name_id[int(id[2])]]]
                        else:
                            pattern_neighbor[name_id[int(id[3])]].append([name_id_person[int(id[0])], name_id[int(id[1])], name_id[int(id[2])]])
                        
            for t in pattern_neighbor:
                pattern_neighbor[t] = list(set([tuple(l) for l in pattern_neighbor[t]]))
            print('check 3.1', flush=True)
            rights, counts = [], np.zeros(id_inc).astype(int)
            all = 0
            for i in range(id_inc):
                if i in pattern_neighbor:
                    for pattern_instance in pattern_neighbor[i]:
                        rights.append(pattern_instance)
                    counts[i] = len(pattern_neighbor[i])
                    all = all + len(pattern_neighbor[i])
            adjs.append((np.concatenate(rights), counts))
            print('check 3.2', flush=True)
            del rights, counts
            gc.collect()
            print('check 3.3', flush=True)
        elif patt == 'PCIC':
            pattern_neighbor = defaultdict(set)
            with open('./data/T20H/pattern/{}.dat'.format(patt), 'r') as file:
                for j, line in enumerate(file):
                    id = line[:-1].split('\t')
                    if j != 0 and int(id[1]) in name_id and int(id[3]) in name_id:
                        if name_id[int(id[1])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[1])]] = [[name_id_person[int(id[0])], name_id_item[int(id[2])], name_id[int(id[3])]]]
                        else:
                            pattern_neighbor[name_id[int(id[1])]].append([name_id_person[int(id[0])], name_id_item[int(id[2])], name_id[int(id[3])]])

                        if name_id[int(id[3])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[3])]] = [[name_id_person[int(id[0])], name_id_item[int(id[2])], name_id[int(id[1])]]]
                        else:
                            pattern_neighbor[name_id[int(id[3])]].append([name_id_person[int(id[0])], name_id_item[int(id[2])], name_id[int(id[1])]])
                        
            for t in pattern_neighbor:
                pattern_neighbor[t] = list(set([tuple(l) for l in pattern_neighbor[t]]))
            print('check 3.1', flush=True)
            rights, counts = [], np.zeros(id_inc).astype(int)
            all = 0
            for i in range(id_inc):
                if i in pattern_neighbor:
                    for pattern_instance in pattern_neighbor[i]:
                        rights.append(pattern_instance)
                    counts[i] = len(pattern_neighbor[i])
                    all = all + len(pattern_neighbor[i])
            adjs.append((np.concatenate(rights), counts))
            print('check 3.2', flush=True)
            del rights, counts
            gc.collect()
            print('check 3.3', flush=True)
        elif patt == 'PCPC':
            pattern_neighbor = defaultdict(set)
            with open('./data/T20H/pattern/{}.dat'.format(patt), 'r') as file:
                for j, line in enumerate(file):
                    id = line[:-1].split('\t')
                    if j != 0 and int(id[1]) in name_id and int(id[3]) in name_id:
                        if name_id[int(id[1])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[1])]] = [[name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[3])]]]
                        else:
                            pattern_neighbor[name_id[int(id[1])]].append([name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[3])]])

                        if name_id[int(id[3])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[3])]] = [[name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[1])]]]
                        else:
                            pattern_neighbor[name_id[int(id[3])]].append([name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[1])]])
                        
            for t in pattern_neighbor:
                pattern_neighbor[t] = list(set([tuple(l) for l in pattern_neighbor[t]]))
            print('check 3.1', flush=True)
            rights, counts = [], np.zeros(id_inc).astype(int)
            all = 0
            for i in range(id_inc):
                if i in pattern_neighbor:
                    for pattern_instance in pattern_neighbor[i]:
                        rights.append(pattern_instance)
                    counts[i] = len(pattern_neighbor[i])
                    all = all + len(pattern_neighbor[i])
            adjs.append((np.concatenate(rights), counts))
            print('check 3.2', flush=True)
            del rights, counts
            gc.collect()
            print('check 3.3', flush=True)
        elif patt == 'PCPCC':
            pattern_neighbor = defaultdict(set)
            with open('./data/T20H/pattern/{}.dat'.format(patt), 'r') as file:
                for j, line in enumerate(file):
                    id = line[:-1].split('\t')
                    if j != 0 and int(id[1]) in name_id and int(id[3]) in name_id and int(id[4]) in name_id:
                        if name_id[int(id[1])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[1])]] = [[name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[3])], name_id[int(id[4])]]]
                        else:
                            pattern_neighbor[name_id[int(id[1])]].append([name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[3])], name_id[int(id[4])]])

                        if name_id[int(id[3])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[3])]] = [[name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[1])], name_id[int(id[4])]]]
                        else:
                            pattern_neighbor[name_id[int(id[3])]].append([name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[1])], name_id[int(id[4])]])

                        if name_id[int(id[4])] not in pattern_neighbor:
                            pattern_neighbor[name_id[int(id[4])]] = [[name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[1])], name_id[int(id[3])]]]
                        else:
                            pattern_neighbor[name_id[int(id[4])]].append([name_id_person[int(id[0])], name_id_person[int(id[2])], name_id[int(id[1])], name_id[int(id[3])]])
                        
            for t in pattern_neighbor:
                pattern_neighbor[t] = list(set([tuple(l) for l in pattern_neighbor[t]]))
            print('check 3.1', flush=True)
            rights, counts = [], np.zeros(id_inc).astype(int)
            all = 0
            for i in range(id_inc):
                if i in pattern_neighbor:
                    for pattern_instance in pattern_neighbor[i]:
                        rights.append(pattern_instance)
                    counts[i] = len(pattern_neighbor[i])
                    all = all + len(pattern_neighbor[i])
            adjs.append((np.concatenate(rights), counts))
            print('check 3.2', flush=True)
            del rights, counts
            gc.collect()
            print('check 3.3', flush=True)
        elif patt in useful_types:
            corners = type_corners[patt]
            two_hops = defaultdict(set)
            for x, neighbors in corners.items():
                for snode in neighbors:
                    for enode in neighbors:
                        if snode!=enode:
                            two_hops[snode].add(enode)
            print('check 3.1', flush=True)
            rights, counts = [], np.zeros(id_inc).astype(int)
            for i in range(id_inc):
                if i in two_hops:
                    current = np.sort(list(two_hops[i]))
                    rights.append(current)
                    counts[i] = len(current)
            adjs.append((np.concatenate(rights), counts))
            print('check 3.2', flush=True)
            del two_hops, rights, counts, type_corners[patt]
            gc.collect()
            print('check 3.3', flush=True)
    print('check 4', flush=True)
    
    if args.attributed=="True": name_attr = np.array([name_attr[id_name[i]] for i in range(len(id_name))]).astype(np.float32)
    if args.attributed == "True": item_attr = np.array([item_attr[id_name_item[i]] for i in range(len(id_name_item))]).astype(np.float32)
    if args.attributed == "True": person_attr = np.array([person_attr[id_name_person[i]] for i in range(len(id_name_person))]).astype(np.float32)

    return adjs, id_name, name_attr, item_attr, person_attr