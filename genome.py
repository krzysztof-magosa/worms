import helpers as h
import collections


class GenomeHandler(object):
    def __init__(self, genes_description):
        self.genes_description = genes_description
        self.count = 0

        index = 0
        self.genes_map = collections.OrderedDict()
        for item in self.genes_description:
            self.genes_map[item["name"]] = slice(index, index + item["count"])
            index += item["count"]
            self.count += item["count"]

    def generate(self, statics=dict()):
        genes = h.generate_bin(self.count)

        for name, value in statics.items():
            genes[self.genes_map[name]] = value

        return genes

    def decode(self, genome):
        assert(len(genome) == self.count)

        data = dict()
        for item in self.genes_description:
            value = h.decode_bin(genome[self.genes_map[item["name"]]])

            if "choices" in item:
                value = item["choices"][int(value)]

            data[item["name"]] = value

        return data
