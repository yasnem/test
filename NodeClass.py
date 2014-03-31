#==============================================================================
# Big class defining everything a basic node in our network needs to be able
# to do and contain as data elements. You will find at the end to methods
# generating random or determined Package objects
#==============================================================================

import numpy as np
import copy
import random
import this  # quit thinking about this module. too hard for you!!
import Package as packet


class Node(object):
    """cool class containing stuff related to nodes"""
    obj_counter = 0  # in order to initiate the node.id

    def __init__(self, size, iteration):
        self._ID = self.__class__.obj_counter
        self._data_stack = []
        self.receive_buffer = []  # package list for incoming data
        self.sending_buffer = []  # list conaining the packages to be send
        self.__class__.obj_counter += 1
        self._sent = 0
        self.packet_history = np.zeros((size, iteration))

    def get_ID(self):
        """id getter"""
        return self._ID

    def get_sent(self):
        """sent setter"""
        return self._sent

    def set_sent(self, value):
        """sent setter"""
        self._sent = value

    def get_data_stack(self):
        """data_stack getter"""
        return self._data_stack

    def set_data_stack(self, data_list):
        """data_stack setter"""
        self._data_stack = data_list

    def check_data_stack(self, data):
        """ checks if a package is known, returns a boolean"""
        assert type(data) == packet.Package
        #======================================================================
        # bool_data = data in self.data_stack
        # return bool_data
        #----------------------------------------------------------------------
        # this does not work..
        #======================================================================
        origin_check = 0
        seq_check = 0
        type_check = 0
        for item in self.data_stack:
            if data.origin == item.origin:
                origin_check = 1
            if data.type == item.type:
                type_check = 1
            if data.seq_number == item.seq_number:
                seq_check = 1
        if origin_check == 0 or seq_check == 0 or type_check == 0:
            return False
        else:
            return True

    def del_sending_buffer(self):
        """clear the sending_buffer list"""
        self.sending_buffer = []

    def del_receive_buffer(self):
        """"same as last function only this time for the receive_buffer"""
        self.receive_buffer = []

    def send_to_neighbor(self, neighbor):
        """ pushes packages in its sending_buffer into the receive_buffer of
        its neighbours"""
        for item in self.sending_buffer:
            if neighbor != item.last_node:
                # deepcopy guarantees everything is copied
                neighbor.receive_buffer.append(copy.deepcopy(item))
                neighbor.receive_buffer[-1].last_node = self

    def update_data(self, column):
        """core function, check all the data in the receive_buffer and if they
        are unknown pushes them into the data_stack and the sending_buffer"""
        for data in self.receive_buffer:
            boolean = self.check_data_stack(data)
            if boolean == False:
                self.data_stack.append(data)
                data.add_to_path(self)
                self.sending_buffer.append(data)
                # the value is stored in the row = to the origin of the packet
                row = data.origin - 1
                self.packet_history[row, column:] = data.value
            elif boolean == True:
                pass

    def init_1_data(self):
        """ creates one package of type height and appends it to
        the data_stack and sending_buffer"""
        new_package = packet.Package(self.ID + 1, 1, self.ID, "height", self)
        new_package.add_to_path(self)
        self.data_stack.append(new_package)
        self.sending_buffer.append(new_package)
        self.packet_history[self.ID, :] = new_package.value

    def init_data(self):  # todo find a way to eliminate these if statements
        """ugly random data generator -.- yet still does what it is supposed
        to do. ONLY for testing; creates random packages """
        init_rand = random.randint(0, 5)
        if init_rand != 0:  # prob of 1 over range of randint()
            pass
        else:
            type_rand = random.randint(1, 3)  # determines the type of package
            data = 5 * random.random()  # actual data
            if type_rand == 1:
                max_seq = 0
                for item in self.data_stack:
                    if item.type == "height" and item.origin == self.ID:
                        if item.seq_number > max_seq:
                            max_seq = item.seq_number
                new_package = packet.Package(data, max_seq + 1, self.ID, "height")
                new_package.add_to_path(self)
            elif type_rand == 2:
                max_seq = 0
                for item in self.data_stack:
                    if item.type == "angles" and item.origin == self.ID:
                        if item.seq_number > max_seq:
                            max_seq = item.seq_number
                new_package = packet.Package(data, max_seq + 1, self.ID, "angles")
                new_package.add_to_path(self)
            elif type_rand == 3:
                max_seq = 0
                for item in self.data_stack:
                    if item.type == "velocity" and item.origin == self.ID:
                        if item.seq_number > max_seq:
                            max_seq = item.seq_number
                new_package = packet.Package(data, max_seq + 1, self.ID, "velocity")
                new_package.add_to_path(self)
            self.data_stack.append(new_package)
            self.sending_buffer.append(new_package)

    sent = property(get_sent, set_sent)
    ID = property(get_ID)
    data_stack = property(get_data_stack, set_data_stack)
