from models import DAGNF
import torch
from timeit import default_timer as timer
import lib.utils as utils
import os
import lib.visualize_flow as vf
import matplotlib.pyplot as plt
import networkx as nx
import UCIdatasets


def batch_iter(X, batch_size, shuffle=False):
    """
    X: feature tensor (shape: num_instances x num_features)
    """
    if shuffle:
        idxs = torch.randperm(X.shape[0])
    else:
        idxs = torch.arange(X.shape[0])
    if X.is_cuda:
        idxs = idxs.cuda()
    for batch_idxs in idxs.split(batch_size):
        yield X[batch_idxs]


def load_data(name):

    if name == 'bsds300':
        return UCIdatasets.BSDS300()

    elif name == 'power':
        return UCIdatasets.POWER()

    elif name == 'gas':
        return UCIdatasets.GAS()

    elif name == 'hepmass':
        return UCIdatasets.HEPMASS()

    elif name == 'miniboone':
        return UCIdatasets.MINIBOONE()

    else:
        raise ValueError('Unknown dataset')


def train(dataset="POWER", load=True, nb_step_dual=100, nb_steps=20, folder="", max_l1=1., nb_epoch=10000,
          network=[200, 200, 200], b_size=100):
    logger = utils.get_logger(logpath=os.path.join(folder, toy, 'logs'), filepath=os.path.abspath(__file__))

    logger.info("Creating model...")

    device = "cpu" if not(torch.cuda.is_available()) else "cuda:0"

    batch_size = b_size

    logger.info("Loading data...")
    data = load_data(dataset)
    data.trn.x = torch.from_numpy(data.trn.x).to(device)
    data.val.x = torch.from_numpy(data.val.x).to(device)
    data.tst.x = torch.from_numpy(data.tst.x).to(device)
    logger.info("Data loaded.")

    dim = data.trn.x.shape[1]
    model = DAGNF(in_d=dim, hiddens_integrand=network, device=device, l1_weight=.01)

    opt = torch.optim.Adam(model.parameters(), 1e-3, weight_decay=1e-5)

    if load:
        logger.info("Loading model...")
        model.load_state_dict(torch.load(toy + '/model.pt'))
        model.train()
        opt.load_state_dict(torch.load(toy + '/ADAM.pt'))
        logger.info("Model loaded.")

    for epoch in range(nb_epoch):
        ll_tot = 0
        start = timer()
        i = 0
        # Training loop
        for cur_x in batch_iter(data.trn.x, shuffle=True, batch_size=batch_size):
            loss = model.loss(cur_x)
            ll_tot += loss.item()
            i += 1
            opt.zero_grad()
            loss.backward(retain_graph=True)
            opt.step()

        ll_tot /= i

        # Testing loop
        ll_test = 0.
        i = 0.
        for cur_x in batch_iter(data.tst.x, shuffle=True, batch_size=batch_size):
            ll, _ = model.compute_ll(cur_x)
            ll_test += ll.mean().item()
            i += 1
        ll_test /= i

        # Update constraints
        if epoch % 1 == 0:
            with torch.no_grad():
                model.dag_embedding.dag.constrainA()

        if epoch % nb_step_dual == 0 and epoch != 0:
            model.update_dual_param()
            if model.l1_weight < max_l1:
                model.l1_weight = model.l1_weight*1.4

        end = timer()

        logger.info("epoch: {:d} - Train loss: {:4f} - Test loss: {:4f} - Elapsed time per epoch {:4f} (seconds)".
                    format(epoch, ll_tot, ll_test, end-start))
        if epoch % 5 == 0:
            # Plot DAG
            A = model.dag_embedding.dag.soft_thresholded_A().detach().cpu().numpy().T
            ax = plt.figure()
            G = nx.from_numpy_matrix(A, create_using=nx.DiGraph)
            pos = nx.layout.spring_layout(G)
            nodes = nx.draw_networkx_nodes(G, pos, node_size=200, node_color='blue', alpha=.7)
            edges, weights = zip(*nx.get_edge_attributes(G, 'weight').items())
            edges = nx.draw_networkx_edges(G, pos, node_size=200, arrowstyle='->',
                                           arrowsize=3, connectionstyle='arc3,rad=0.2',
                                           edge_cmap=plt.cm.Blues, width=5*weights)
            labels = {}
            for i in range(dim):
                labels[i] = str(r'$%d$' % i)
            nx.draw_networkx_labels(G, pos, labels, font_size=12)

            #vf.plt_flow(model.compute_ll, ax)
            plt.savefig("%s%s/flow_%d.pdf" % (folder, toy, epoch))
            torch.save(model.state_dict(), folder + toy + '/model.pt')
            torch.save(opt.state_dict(), folder + toy + '/ADAM.pt')
            G.clear()
            plt.clf()
            print(A)

import argparse
datasets = ["power"]

parser = argparse.ArgumentParser(description='')
parser.add_argument("-dataset", default=None, choices=datasets, help="Which toy problem ?")
parser.add_argument("-load", default=False, action="store_true", help="Load a model ?")
parser.add_argument("-folder", default="", help="Folder")
parser.add_argument("-nb_steps_dual", default=100, type=int, help="number of step between updating Acyclicity constraint and sparsity constraint")
parser.add_argument("-max_l1", default=1., type=float, help="Maximum weight for l1 regularization")
parser.add_argument("-nb_epoch", default=10000, type=int, help="Number of epochs")
parser.add_argument("-b_size", default=100, type=int, help="Batch size")
parser.add_argument("-network", default=[100, 100, 100, 100], nargs="+", type=int, help="NN hidden layers")

args = parser.parse_args()


if args.dataset is None:
    toys = datasets
else:
    toys = [args.dataset]

for toy in toys:
    if not(os.path.isdir(args.folder + toy)):
        os.makedirs(args.folder + toy)
    train(toy, load=args.load, folder=args.folder, nb_step_dual=args.nb_steps_dual, max_l1=args.max_l1,
              nb_epoch=args.nb_epoch, network=args.network, b_size=args.b_size)
