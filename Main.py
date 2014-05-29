#=============================================================================
# this is the main file importing all other files and classes and executing all of it
#=============================================================================
# hello world!
import networkx as nx
import matplotlib.pyplot as plt
import Graph
import NodeClass as nde
import SBAClass as sba
import AHBPClass as ahbp
import random
import numpy as np
from collections import OrderedDict
# from mpl_toolkits.mplot3d import axes3d
# from scipy.interpolate import griddata


def check_nodes(graph):
    """
    Check if all nodes in the graph already got all messages

    Note that the criterium for having all nodes is rather easy since we
    initialize all nodes with only  one message at the beginning.
    Thus at the end the data_stack has to contain 10 different messages.

    Arguments:
    graph -- networkx Graph object

    Return-type:
    True -- if all nodes contain all messages
    False -- if not everything is known to all messages
    """
    size = len(graph)
    for node in graph.nodes_iter():
        if len(node.data_stack) == size:
            pass
        elif len(node.data_stack) < size:
            return False
    return True


def get_message_counter(graph):
    """
    Compute the total number of sent messages in the network

    Iterate through all the nodes in the network and add up their
    message_counter to get the total number.

    Arguments:
    graph -- networkx Graph representing the network

    Return-type:
    total_number -- total number of sent messages
    """
    total_number = 0
    max_number = 0
    for node in graph.nodes():
        if max(node.message_counter) > max_number:
            max_number = max(node.message_counter)
        for number in node.message_counter:
            total_number += number
    # delete comment for use later
    return total_number, max_number


def setup_sending_flooding(graph):
    """
    Perfrom the sending process according to pure flooding

    Iterates through all nodes in the graph.
    The sending part and message-updating part are split.
    -> a message is not rebroadcasted mulitpletimes in the same iteration

    Arguments:
    graph -- a graph with node instances as vertices
    iteration -- number of iteration done during the sending
    FLAG -- string which indicates the broadcast algorithm

    Return-type:
    none
    """
    flag = 'flooding'
    # initate all nodes with a datapacket
    for node in graph.nodes():
        node.init_1_data()
    # loop through all nodes and their neighbours and push data from
    # its own sending_buffer to its neighbour's receive_buffer
    iteration = 0
    while not check_nodes(graph):
        for node in graph.nodes():
            # check if node rebroadcasts any messages
            for neigh in graph.neighbors_iter(node):
                node.send_to_neighbor(neigh)
        # before updating the sending_buffer delete already sent data
        # after update del receive_buffer not to check already known data twice
        for node in graph.nodes():
            node.del_sending_buffer()
            node.update_data(flag)
            node.del_receive_buffer()
        iteration += 1
        #Graph.print_all_data_stacks(graph)


def setup_sending_SBA(graph, timer):
    """
    Perform the sending process according to the SBA

    Iterates through all nodes in the graph.
    The sending part and message-updating part are split.
    -> a message is not rebroadcasted mulitpletimes in the same iteration
    Message-updating:
    - Check vertex-message pairs with an active random timer
    - After sending check the receive-buffer for unknown messages

    Arguments:
    graph -- a graph with node instances as vertices
    iteration -- number of iteration done during the sending
    FLAG -- string which indicates the broadcast algorithm

    Return-type:
    none
    """
    flag = 'SBA'
    # initiate all nodes with a data packet
    for node in graph.nodes():
        node.init_1_data()
        node.build_2_hop(graph)
    # update each packet_dict, containing all the packets
    # that currently have an active random timer
    iteration = 0
    while not check_nodes(graph):
        for node in graph.nodes():
            sba.check_receive_buffer(node, iteration, timer)
        for node in graph.nodes():
            sba.update_packet_dict(node, iteration)
        # forward packet in the sending list to neighbors
        for node in graph.nodes():
            # check if node rebroadcasts any messages
            for neigh in graph.neighbors_iter(node):
                node.send_to_neighbor(neigh)
            node.del_sending_buffer()
        # # checks incoming packets if they are already known and adds
        # # them if necessary to the packet dict and activates a timer
        # for node in graph.nodes():
        #     for packet in node.receive_buffer:
        #         sba.check_receive_buffer(node, packet, iteration, graph, timer)
        # # before updating the sending_buffer delete already sent data
        # # after update del receive_buffer not to check already known data twice
        # for node in graph.nodes():
        #     node.del_sending_buffer()
        #     node.update_data(flag)
        #     node.del_receive_buffer()
        iteration += 1
    return iteration


def setup_sending_AHBP(graph):
    """
    Perfrom the sending process according to the AHBP

    Iterates through all nodes in the graph.
    The sending part and message-updating part are split.
    -> a message is not rebroadcasted mulitpletimes in the same iteration
    Message-updating:Check the receive-buffer and if needed build the BRG-set

    Arguments:
    graph -- a graph with node instances as vertices
    iteration -- number of iteration done during the sending
    timer -- parameter for the random-timer

    Return-type:
    none
    """
    # initiate the nodes with a data packet
    for node in graph.nodes_iter():
        node.init_1_data()
        # only use this until hello protocol is implemented
        # this gets the 2-hop neighbor hood form the 'master'-graph
        node.build_2_hop(graph)
        # with open("node_" + str(node.ID + 1) + '.txt', 'w') as outfile:
        #     outfile.write("new file for node :" + str(node.ID + 1) + "\n")

    iteration = 0
    while not check_nodes(graph):
        # split up the process of checking the receive_buffer
        # and sending to neighbor, such that can only traverse
        # one edge during an iteration step

        for node in graph.nodes():
            ahbp.check_receive_buffer(node, iteration)
            node.del_receive_buffer()

            # for all messages in the sending_buffer build the BRG-Set
            for message in node.sending_buffer:
                ahbp.build_BRG(node, message)

        if check_nodes(graph):
            break

        # rebroadcast the messages in the sending_buffer to the neighbors
        for node in graph.nodes_iter():
            # check if node rebroadcasts any messages
            for neigh in node.two_hop_dict:
                node.send_to_neighbor(neigh)
            node.del_sending_buffer()
        iteration += 1


def setup_sending_half_sba(graph):
    """
    Perform the sending process according to parts of the SBA

    The parts with the random
    """
    for node in graph.nodes():
        node.init_1_data()
        node.build_2_hop(graph)

    iteration = 0
    while not check_nodes(graph):
        for node in graph.nodes():
            # check if node rebroadcasts any messages
            for neigh in graph.neighbors_iter(node):
                node.send_to_neighbor(neigh)
            node.del_sending_buffer()

        for node in graph.nodes_iter():
            for message in node.receive_buffer:
                boolean = node.check_data_stack(message)
                if not boolean:
                    message.add_to_path(node)
                    node.data_stack.append(message)
                    if not sba.check_neigh(node, message.last_node):
                       node.sending_buffer.append(message)

            node.del_receive_buffer()
        iteration += 1


def setup_graph(laplacian):
    """
    Create a graph object with Node-instances according to the laplacian

    Arguments:
    laplacian -- numpy.array with the laplacian matrix of the graph
    iteration -- number of iteration for the sending-history (default = 0)

    Return-type:
    my_graph -- networkx Graph object
    """
    nde.Node.obj_counter = 0
    # this block adds the nodes to the graph and creates two dict
    # in order to label the graph correctly
    size = len(laplacian[0, :])
    my_graph = nx.Graph()
    for i in range(size):
        # depending on the mode add the arguments in the node initiator
        my_graph.add_node(nde.Node(), name=str(i + 1), color='blue')
        #my_graph.add_node(nde.Node(size, iteration), name=str(i + 1))
    # stores the nodes and their name attributes in a dictionary
    nodes_names = nx.get_node_attributes(my_graph, "name")
    # switches key and values--> thus names_nodes
    names_nodes = dict(zip(nodes_names.values(), nodes_names.keys()))

    # this block adds the edges between the nodes
    for i in range(0, size):
        for j in range(i + 1, size):
            if laplacian[i, j] == -1:
                node_1 = names_nodes[str(i + 1)]
                node_2 = names_nodes[str(j + 1)]
                my_graph.add_edge(node_1, node_2)

    return my_graph


def create_figure(graph):
    """Call other functions to create the plots"""
    Graph.iteration_plots(graph)

    # # creates all the animated plots for the nodes
    # size = len(graph.nodes())
    # for i in range(size):
    #     fig = plt.figure()
    #     Graph.bar_plot(graph, i + 1, fig)

    print 'check plot generating'


def get_num_sender(graph):
    """Iterate through graph and count true sender flags"""
    rebroadcaster = 0
    for node in graph.nodes_iter():
        if node.sender:
            rebroadcaster += 1
    return rebroadcaster


def average_degree(graph):
    """Compute the average degree of all the vertices in the graph"""
    av_deg = 0
    for node in graph.nodes_iter():
        av_deg += graph.degree(node)
    av_deg /= float(len(graph))
    return av_deg


def clear_graph_data(graph):
    """Clear counter, flags and messages in the graph"""
    for node in graph.nodes_iter():
        node.del_sending_buffer()
        node.del_receive_buffer()
        node.del_data_stack()
        node.sender = False
        node.message_counter = []


def random_graph(num_nodes):
    laplacian_array = build_rand_graph(num_nodes)
    rand_graph = setup_graph(laplacian_array)
    return rand_graph, laplacian_array


def build_line_laplacian(size):
    """
    Build laplacian of line-graph and return it as numpy.array"""
    my_ar = np.eye(size)
    if size == 2:
        my_ar = np.array([[1, -1],
                          [-1, 1]])
    for i in range(1, size-1):
        my_ar[i, i] += 1
        my_ar[i-1, i] = -1
        my_ar[i+1, i] = -1
        my_ar[i, i-1] = -1
        my_ar[i, i+1] = -1
    return my_ar


def get_connectivity(laplacian):
    """
    Compute the algebraic connectivity of a graph

    Arguments:
    laplacian -- Laplace matrix of a graph

    Return-type:
    connectivity -- float; algebraic connectivity
    """
    val, vec = np.linalg.eig(laplacian)
    val.sort()
    return val[1]


def test_connectivity_degree():
    conn_dict = {}
    for i in range(1000):
        graph, laplacian = random_graph(6)
        Graph.print_graph(graph)
        con = get_connectivity(laplacian)
        deg = average_degree(graph)
        con = abs(con)
        con = round(con, 3)
        if con not in conn_dict:
            conn_dict[con] = [0, 0]
        conn_dict[con][0] += deg
        conn_dict[con][1] += 1
    for a in conn_dict:
        conn_dict[a] = float(conn_dict[a][0]/conn_dict[a][1])

    con_lst = OrderedDict(sorted(conn_dict.items()))
    print con_lst


def test_connectivity():
    conn_dict = {}
    conn_lst = []
    for i in range(1000):
        graph, laplacian = random_graph(6)
        con = get_connectivity(laplacian)
        conn_lst.append(nx.average_node_connectivity(graph))
        conn_lst.sort()
        print con
        # if con < 0.74 and con>0.73:
        #     Graph.print_graph(graph)
        if 0.43 < con < 0.45:
            Graph.print_graph(graph)
        con = abs(con)
        con = round(con, 3)
        if con not in conn_dict:
            conn_dict[con] = 0
        conn_dict[con] += 1
    con_lst = OrderedDict(sorted(conn_dict.items()))
    print conn_lst
    print con_lst


def do_plots(flood_lst, ahbp_lst, sba_lst, half_sba, ax, mode):
    conn_flood, y_flood, flood_err = sort_dict(flood_lst)
    conn_ahbp, y_ahbp, ahbp_err = sort_dict(ahbp_lst)
    conn_sba, y_sba, sba_err = sort_dict(sba_lst)
    conn_half_sba, y_half_sba, half_sba_err = sort_dict(half_sba)

    ax.errorbar(conn_flood, y_flood, yerr=flood_err, marker='o')
    ax.errorbar(conn_ahbp, y_ahbp, yerr=ahbp_err, color='red', marker='s')
    ax.errorbar(conn_half_sba, y_half_sba, yerr=half_sba_err, color='green', marker='^')
    ax.errorbar(conn_sba, y_sba, yerr=sba_err, color='orange', marker='D', capthick=3)

    ax.xaxis.set_label_text('Graph size')
    if mode == 1:
        ax.yaxis.set_label_text('Rebroadcaster')
    elif mode == 2:
        ax.yaxis.set_label_text('Messages sent')
    elif mode == 3:
        ax.yaxis.set_label_text('Max Bufferlength')


def sort_dict(raw_dict):
    """
    Sort the tuples in the list and unzip it into connectivity and y-value

    Argument:
    raw_dict -- dict with key: connectivity; values: [y-average, y-std]

    Return-types:
    conn_lst -- lst containing the connectivity values
    y_lst -- lst containing the average
    y_error -- lst containint the standart deviation
    """
    ordered_lst = OrderedDict(sorted(raw_dict.items()))
    conn_lst = ordered_lst.keys()
    y_lst = [a[0] for a in ordered_lst.values()]
    y_error = [a[1] for a in ordered_lst.values()]
    return conn_lst, y_lst, y_error


def average_std(value_dict):
    """
    Compute the average and std for the values of the input dictionary

    Argument:
    value_dict -- dictionary with key: connectivity; values: [ measured values ]

    Return-type:
    value_dict -- dictionary now with key: connectivity; values: [ average, std ]
    """
    for number in value_dict:
        average = np.average(value_dict[number])
        deviation = np.std(value_dict[number])
        value_dict[number] = [average, deviation]
    return value_dict


def update_dict(mes_dict, rebroad_dict, max_dict, conn, rebroad, mes, max_mes):
    """
    Check if conn is already key and append rebroad, mes

    Argument:
    mes_dict -- dictionary containing the total number of messages
    rebroad_dict -- dictionary conatining the number of rebroadcaster
    conn -- connectivity of the graph
    rebroad -- number of rebroadcaster measured for the sample
    mes -- total messages measured for the sample

    Return-type:
    rebroad_dict -- updated rebroad_dict
    mes_dict -- updated message_dict
    """
    if conn not in mes_dict:
        mes_dict[conn] = []
    if conn not in rebroad_dict:
        rebroad_dict[conn] = []
    if conn not in max_dict:
        max_dict[conn] = []

    max_dict[conn].append(max_mes)
    mes_dict[conn].append(mes)
    rebroad_dict[conn].append(rebroad)
    return rebroad_dict, mes_dict, max_dict

def test_sba():
    max_size = 6
    samples = 2000

    fig = plt.figure('sba')
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)
    x_lst = []
    messages = []
    rebroadcaster = []
    for i in range(samples):
        graph, laplacian = random_graph(max_size)
        # graph dont makes any sense right now, cuz x-lst is not right
        x_lst.append(get_connectivity(laplacian))
        if 1.4 > x_lst[-1] > 1.3:
            setup_sending_SBA(graph, 5)
            mes_num, max_mes = get_message_counter(graph)
            messages.append(mes_num)
            rebroadcaster.append(get_num_sender(graph))
        # if 1.1 > x_lst[-1] > 0.9:
            print x_lst[-1], messages[-1], rebroadcaster[-1]
            # Graph.print_graph(graph)
    print x_lst
    print messages
    print rebroadcaster
    mx = zip(x_lst, messages)
    mx.sort()
    xm, messages = zip(*mx)

    rx = zip(x_lst, rebroadcaster)
    rx.sort()
    xr, rebroadcaster = zip(*rx)
    print xm, messages
    print xr, rebroadcaster

    ax1.plot(xm, messages, marker='o')
    ax2.plot(xr, rebroadcaster, marker='o')
    plt.show()



def test_plots():
    max_size = 20
    # samples = 100

    x_lst = [i for i in range(10, max_size+1)]

    fig1 = plt.figure('Total messages')
    fig2 = plt.figure('Number of rebroadcaster')
    fig3 = plt.figure('Max buffer-length')

    for size in x_lst:
        print size
        ax1 = fig1.add_subplot(max_size/2, 2, size-1)
        ax2 = fig2.add_subplot(max_size/2, 2, size-1)
        ax3 = fig3.add_subplot(max_size/2, 2, size-1)

        flood_mes = {}
        ahbp_mes = {}
        sba_mes = {}
        half_sba_mes = {}

        flood_rebroad = {}
        ahbp_rebroad = {}
        sba_rebroad = {}
        half_rebroad = {}

        flood_max = {}
        ahbp_max = {}
        sba_max = {}
        half_sba_max = {}

        # for a in range(samples):
        for a in range(10):
            conn = -1
            while conn < 0.5:
                graph, laplacian = random_graph(size)
                conn = round(get_connectivity(laplacian), 2)
            # get values for flooding
            print 'flooding'
            setup_sending_flooding(graph)
            messages, max_mes = get_message_counter(graph)
            rebroadcaster = get_num_sender(graph)
            flood_rebroad, flood_mes, flood_max = update_dict(flood_mes, flood_rebroad, flood_max, conn, rebroadcaster, messages, max_mes)
            # set all the sender flags to false again
            # so one can reuse the same graph
            clear_graph_data(graph)
            # get values for AHBP
            print 'ahbp'
            setup_sending_AHBP(graph)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            ahbp_rebroad, ahbp_mes, ahbp_max = update_dict(ahbp_mes, ahbp_rebroad, ahbp_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)
            # get values for SBA
            print 'half_sba'
            setup_sending_half_sba(graph)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            half_rebroad, half_sba_mes, half_sba_max = update_dict(half_sba_mes, half_rebroad, half_sba_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)
            print 'sba'
            iteration = setup_sending_SBA(graph, 2)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            sba_rebroad, sba_mes, sba_max = update_dict(sba_mes, sba_rebroad, sba_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)

        # print flood_mes

        flood_mes = average_std(flood_mes)
        ahbp_mes = average_std(ahbp_mes)
        half_sba_mes = average_std(half_sba_mes)
        sba_mes = average_std(sba_mes)

        flood_rebroad = average_std(flood_rebroad)
        ahbp_rebroad = average_std(ahbp_rebroad)
        sba_rebroad = average_std(sba_rebroad)
        half_rebroad = average_std(half_rebroad)


        flood_max = average_std(flood_max)
        ahbp_max = average_std(ahbp_max)
        half_sba_max = average_std(half_sba_max)
        sba_max = average_std(sba_max)

        do_plots(flood_max, ahbp_max, sba_max, half_sba_max, ax3, 3)

        do_plots(flood_mes, ahbp_mes, sba_mes, half_sba_mes, ax1, 2)

        do_plots(flood_rebroad, ahbp_rebroad, sba_rebroad, half_rebroad, ax2, 1)

    # sometimes one needs to hack a lil bit
    lines1 = fig1._axstack._elements[0][1][1].lines
    lines2 = fig2._axstack._elements[0][1][1].lines
    lines3 = fig3._axstack._elements[0][1][1].lines

    fig1.legend((lines1[2], lines1[5], lines1[8], lines1[11]),
                ('flood', 'ahbp', 'half_sba', 'sba'), 'lower right')
    fig2.legend((lines2[2], lines2[5], lines2[8], lines2[11]),
                ('flood', 'ahbp', 'half_sba', 'sba'), 'lower right')
    fig3.legend((lines3[2], lines3[5], lines3[8], lines3[11]),
                ('flood', 'ahbp', 'half_sba', 'sba'), 'lower right')
    plt.show()


def test_rebroadcasting():
    y_flood = []
    y_ahbp = []
    y_sba = []
    y_message_flood = []
    y_message_ahbp = []
    y_message_sba = []
    x_lst = [i for i in xrange(2, 16)]
    print x_lst
    for i in x_lst:
        laplacian = build_line_laplacian(i)
        graph = setup_graph(laplacian)
        # get values for flooding

        print 'flooding'
        setup_sending_flooding(graph, 'flooding')
        flood_rebroadcast = get_num_sender(graph)
        mes_num, max_mes = get_message_counter(graph)
        y_message_flood.append(mes_num)
        # set all the sender flags to false again
        # so one can reuse the same graph
        clear_graph_data(graph)
        # get values for ahbp
        print 'ahbp'
        setup_sending_AHBP(graph)
        ahbp_rebroadcast = get_num_sender(graph)
        mes_num, max_mes = get_message_counter(graph)
        y_message_ahbp.append(mes_num)
        clear_graph_data(graph)

        print 'sba'
        setup_sending_half_sba(graph)
        sba_rebroadcast = get_num_sender(graph)
        mes_num, max_mes = get_message_counter(graph)
        y_message_sba.append(mes_num)
        clear_graph_data(graph)

        y_flood.append(flood_rebroadcast)
        y_ahbp.append(ahbp_rebroadcast)
        y_sba.append(sba_rebroadcast)

    fig = plt.figure(1)
    plt.plot(x_lst, y_flood, label='flood', marker='o')
    plt.plot(x_lst, y_ahbp, color='red', label='ahbp', marker='o')
    plt.plot(x_lst, y_sba, color='green', label='sba', marker='o')
    plt.legend(loc='upper left')

    fig2 = plt.figure()
    plt.plot(x_lst, y_message_flood, label='flood', marker='o')
    plt.plot(x_lst, y_message_ahbp, color='red', label='ahbp', marker='o')
    plt.plot(x_lst, y_message_sba, color='green', label='sba', marker='o')
    plt.legend(loc='upper left')

    plt.show()

    fig.savefig('line_rebroadcast.svg')
    fig2.savefig('line_message.svg')


def sender_plot():  # TODO add some other plots in this function
    """
    Plot the number of rebroadcasting nodes in the network

    Generate for every graph size a certain number of random graphs
    and perform the sending process in order to gather the number of
    rebroadcasting nodes. For SBA gather 3-times more data
    since it has a random timer.
    Then plot the average and a boxplot for each graph size

    function parameters:
    max_nodes -- up to which network size data should gathered
    samples -- number of samples per graph size

    Return-type:
    Stores the plots as png.
    """
    max_nodes = 10
    samples = 10
    x_lst = [i for i in xrange(2, max_nodes)]
    y_flood = np.zeros((samples, max_nodes-2))
    y_ahbp = np.zeros((samples, max_nodes-2))
    y_sba = np.zeros((3*samples, max_nodes-2))
    y_flood_mean = []
    y_ahbp_mean = []
    y_sba_mean = []
    y_deg_flood_ahbp = []
    y_deg_sba = []
    y_message_flood = []
    y_message_ahbp = []
    y_message_sba = []
    y_connectivity_flood_ahbp = []
    y_conectitvity_sba = []
    for i in x_lst:
        print i
        flood_rebroadcast = 0
        sba_rebroadcast = 0
        ahbp_rebroadcast = 0
        flood_ahbp_deg = 0
        sba_deg = 0
        # get the average of rebbroadcasting nodes over three different graph
        # because the degree_lst may vary quite a lot
        for a in range(samples):
            # build random graph
            rand_graph, laplacian = random_graph(i)

            val, vec = np.linalg.eig(laplacian)
            val.sort()
            y_connectivity_flood_ahbp.append(val[1])
            y_conectitvity_sba.append(val[1])
            # nx.draw(rand_graph, with_labels=False)
            # plt.show()
            flood_ahbp_deg += average_degree(rand_graph)
            sba_deg += average_degree(rand_graph)
            # get values for flooding
            setup_sending_flooding(rand_graph, 'flooding')
            y_flood[a, i-2] = get_num_sender(rand_graph)
            flood_rebroadcast += get_num_sender(rand_graph)
            mes_num, max_mes = get_message_counter(rand_graph)
            y_message_flood.append(mes_num)
            # set all the sender flags to false again
            # so one can reuse the same graph
            clear_graph_data(rand_graph)
            # get values for ahbp
            setup_sending_AHBP(rand_graph)
            y_ahbp[a, i-2] = get_num_sender(rand_graph)
            ahbp_rebroadcast += get_num_sender(rand_graph)
            mes_num, max_mes = get_message_counter(rand_graph)
            y_message_ahbp.append(mes_num)
            clear_graph_data(rand_graph)

            setup_sending_SBA(rand_graph, 2, 'SBA')
            y_sba[a, i-2] = get_num_sender(rand_graph)
            sba_rebroadcast += get_num_sender(rand_graph)
            mes_num, max_mes = get_message_counter(rand_graph)
            y_message_sba.append(mes_num)
            clear_graph_data(rand_graph)
            # SBA has a random timer get some more samples for an accurate result
            for b in range(2):
                rand_graph, laplacian = random_graph(i)

                val, vec = np.linalg.eig(laplacian)
                val.sort()
                y_conectitvity_sba.append(val[1])

                sba_deg += average_degree(rand_graph)
                setup_sending_SBA(rand_graph, 2, 'SBA')
                y_sba[a*3 + b + 1, i-2] = get_num_sender(rand_graph)
                sba_rebroadcast += get_num_sender(rand_graph)

        y_flood_mean.append(flood_rebroadcast/float(samples))
        y_ahbp_mean.append(ahbp_rebroadcast/float(samples))
        y_sba_mean.append(sba_rebroadcast/float(3*samples))

        y_deg_flood_ahbp.append(flood_ahbp_deg/float(samples))
        y_deg_sba.append(sba_deg/float(3*samples))
    # print np.std(y_flood, axis=1)
    # print y_ahbp
    # print y_sba
    # print y_flood_mean
    # print y_ahbp_mean
    # print y_sba_mean

    # fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, sharey=True)
    # # ax1.errorbar(x_lst, y_flood_mean, y_flood, ecolor='red')
    # ax1.plot(x_lst, y_flood_mean, y_ahbp_mean, y_sba_mean)
    # # ax1.boxplot(y_flood)
    # ax1.set_title('pure flooding')
    #
    # # ax2.boxplot(y_ahbp)
    # # ax1.plot(x_lst, y_ahbp_mean, color='red')
    # # ax2.errorbar(x_lst, y_ahbp_mean, y_ahbp, ecolor='red')
    # ax2.set_title('ad-hoc broadcast protocol')
    #
    # # ax3.errorbar(x_lst, y_sba_mean, y_sba, ecolor='red')
    # # ax3.boxplot(y_sba)
    # # ax1.plot(x_lst, y_sba_mean, color='green')
    # ax3.set_title('scalabe broadcast algorithm')
    # x_pos = [i for i in range(1, x_lst[-1]+1)]
    # # plt.xticks(x_pos, x_lst)
    # # plt.ylim(0, x_lst[-1])
    fig = plt.figure(1)
    plt.plot(x_lst, y_flood_mean, label='flood')
    plt.plot(x_lst, y_ahbp_mean, color='red', label='ahbp')
    plt.plot(x_lst, y_sba_mean, color='green', label='sba')
    plt.legend()
    fig2, (axi1, axi2) = plt.subplots(2, sharex=True, sharey=True)
    axi1.plot(x_lst, y_deg_flood_ahbp)
    axi1.set_title('average degree for flooding and ahbp')

    axi2.plot(x_lst, y_deg_sba)
    axi2.set_title('average degree for sba graphs')

    fig3 = plt.figure()
    plt.plot(x_lst, y_message_flood, label='flood')
    plt.plot(x_lst, y_message_ahbp, color='red', label='ahbp')
    plt.plot(x_lst, y_message_sba, color='green', label='sba')
    plt.legend()

    plt.show()

    fig.savefig('sender_plots.svg')
    fig2.savefig('degree_plots.svg')
    fig3.savefig('message_plot.svg')


def lattice_graph(length):
    """
    Build a hexagonally gridded graph of a square shaped form

    The grid has a squared shape of size = length.
    First create a square grid graph then add edges on the diagonals.

    Arguments:
    length -- integer determining the size of the square

    Return-type:
    graph -- networkx.Graph object
    """
    # builds a square grid graph
    graph = nx.grid_2d_graph(length, length)
    # in each square add an edge on the diagonal -> hexagonal shape
    # add edges to seperate list, cuz cannot modifiy the graph during iteration
    edge_lst = []
    for n in graph:
        x, y = n
        if y > 0 and x < length-1:
            edge_lst.append((n, (x+1, y-1)))
    graph.add_edges_from(edge_lst)
    return graph


def build_rand_graph(num_nodes):
    """
    Build the DFA-like random graph

    First build a hexagonally gridded graph -> call 'lattice_graph()'
    Then delete random nodes till num_nodes nodes remain.
    If deleting a node results in cutting the graph into mutliple components
    check if one of the subgraphs has still enough vertices.
    Continue computation with this subgraph.
    Else delete another vertex.
    Return the laplacian representation of the graph

    Arguments:
    num_nodes -- number of nodes the resulting graph should have

    Return-type:
    laplacian-matrix -- numpy array
    """
    # root = math.sqrt(num_nodes)
    # length = int(math.ceil(root))
    graph = lattice_graph(num_nodes)
    # for node_name in graph.node:
    #     graph.node[node_name]['color'] = 'red'
    # pos = nx.spring_layout(graph)
    while len(graph) > num_nodes:
        # as long as the graph is not connect
        # after removing a node try another one
        connect_bool = False
        while not connect_bool:
            node_index = random.randint(0, len(graph)-1)
            removed_node = graph.nodes()[node_index]
            removed_edges = graph.edges(removed_node)
            # graph.node[removed_node]['color'] = 'blue'
            # colors = []
            # for node_name in graph.node:
            #     colors.append(graph.node[node_name]['color'])
            # nx.draw(graph,pos, node_color=colors)
            # plt.show()
            graph.remove_node(removed_node)
            # check if graph is still connected
            connect_bool = nx.is_connected(graph)
            if not connect_bool:
                sub_graphs_worked = False
                sub_graphs = nx.connected_component_subgraphs(graph)
                for sub in sub_graphs:
                    if len(sub) >= num_nodes:
                        sub_graphs_worked = True
                        break
                if sub_graphs_worked:
                    # for node_name in sub:
                    #     graph.node[node_name]['color'] = 'blue'
                    # colors = []
                    # for node_name in graph.node:
                    #     colors.append(graph.node[node_name]['color'])
                    # nx.draw(graph,pos, node_color=colors)
                    # plt.show()
                    # take on purpose the last sub element from the for-loop
                    graph = sub
                    connect_bool = True
                    # for node_name in graph.node:
                    #     graph.node[node_name]['color'] = 'red'

            # if graph is not connected anymore put removed node back
                else:
                    graph.add_node(removed_node)  # , color = 'red')
                    graph.add_edges_from(removed_edges)

    # nx.draw(graph)
    # plt.show()

    laplacian_matrix = nx.laplacian_matrix(graph)
    return laplacian_matrix.getA()

FLAG = ""


def main():
    """main function which performs the whole retransmission"""
    # test_connectivity()
    # test_3d_plot()
    # test_connectivity_degree()dimensions of matplotlib 3d plots arguments
    # test_rebroadcasting()
    test_sba()
    # test_plots()
    # # laplacian matrix -> has the information about the network-topology
    # graph_matrix = np.array([[ 3, -1,  0, -1, -1,  0,  0,  0,  0,  0,  0,  0,  0],
    #                          [-1,  3, -1, -1,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    #                          [ 0, -1,  4, -1,  0,  0, -1, -1,  0,  0,  0,  0,  0],
    #                          [-1, -1, -1,  6, -1, -1, -1,  0,  0,  0,  0,  0,  0],
    #                          [-1,  0,  0, -1,  3, -1,  0,  0,  0,  0,  0, -1,  0],
    #                          [ 0,  0,  0, -1, -1,  5, -1,  0,  0, -1, -1, -1,  0],
    #                          [ 0,  0, -1, -1,  0, -1,  6, -1, -1, -1,  0,  0,  0],
    #                          [ 0,  0, -1,  0,  0,  0, -1,  3, -1,  0,  0,  0,  0],
    #                          [ 0,  0,  0,  0,  0,  0, -1, -1,  3, -1,  0,  0,  0],
    #                          [ 0,  0,  0,  0,  0, -1, -1,  0, -1,  5, -1,  0, -1],
    #                          [ 0,  0,  0,  0,  0, -1,  0,  0,  0, -1,  4, -1, -1],
    #                          [ 0,  0,  0,  0, -1, -1,  0,  0,  0,  0, -1,  3,  0],
    #                          [ 0,  0,  0,  0,  0,  0,  0,  0,  0, -1, -1,  0,  2]])
    # val, vec = np.linalg.eig(graph_matrix)
    # val.sort()
    # print val[1]

    #==========================================================================
    # graph_matrix = np.array([[ 2, -1,  0,  0, -1,  0],
    #                          [-1,  3, -1,  0, -1,  0],
    #                          [ 0, -1,  2, -1,  0,  0],
    #                          [ 0,  0, -1,  3, -1, -1],
    #                          [-1, -1,  0, -1,  3,  0],
    #                          [ 0,  0,  0, -1,  0,  1]])
    #==========================================================================
    # graph_matrix = np.array([[ 6, -1, -1, -1, -1, -1, -1],
    #                          [-1,  3, -1,  0,  0,  0, -1],
    #                          [-1, -1,  3, -1,  0,  0,  0],
    #                          [-1,  0, -1,  3, -1,  0,  0],
    #                          [-1,  0,  0, -1,  3, -1,  0],
    #                          [-1,  0,  0,  0, -1,  3, -1],
    #                          [-1, -1,  0,  0,  0, -1, 3]])

    # graph_matrix = np.array([[4, -1, -1, -1, -1, 0],
    #                          []])
    # my_graph = setup_graph(graph_matrix, ITERATION)
    # print nx.average_node_connectivity(my_graph)
    # print nx.laplacian_matrix(my_graph)
    # print nx.clustering(my_graph)
    # build_rand_graph(5)
    # Graph.print_graph(my_graph)
    # while True:
    #     clear_graph_data(my_graph)
    #     print "Your options are as follows:\n\n"\
    #       "flooding ->\tPure Flooding in the Network\n"\
    #       "SBA ->\t\tScalable Broadcast Algorithm\n"\
    #       "AHBP ->\t\tAd-Hoc Broadcast Protocol\n"
    #     FLAG = raw_input("Enter your Flag. To quit press enter\n")
    #     if FLAG == "":
    #         print 'Application is now shutting down'
    #         break
    #     elif FLAG == "SBA":
    #         setup_sending_SBA(my_graph, ITERATION, FLAG)
    #         print get_num_sender(my_graph)
    #         set_sender_false(my_graph)
    #         print 'check SBA calculations'
    #     elif FLAG == "AHBP":
    #         setup_sending_AHBP(my_graph, ITERATION)
    #         print get_num_sender(my_graph)
    #         set_sender_false(my_graph)
    #         print 'check AHBP calculations'
    #     elif FLAG == "flooding":
    #         setup_sending_flooding(my_graph, ITERATION, FLAG)
    #         print get_num_sender(my_graph)
    #         set_sender_false(my_graph)
    #         print 'check flooding calculations'
    #     create_figure(my_graph)


if __name__ == '__main__':
    main()
