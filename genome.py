import helpers as h
import collections


class GenomeHandler(object):
    def __init__(self, genes):
        self.genes = genes
        self.count = 0

        index = 0
        self.genes_map = collections.OrderedDict()
        for name, item in genes.items():
            self.genes_map[name] = slice(index, index + item["count"])
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
        for name, item in self.genes.items():
            base = 1.0

            if "base" in item:
                base = item["base"]

            if "dict" in item:
                base = None

            value = h.decode_bin(
                genome[self.genes_map[name]],
                base=base
            )

            if "type" in item:
                if item["type"] == "int":
                    value = int(value)
                else:
                    raise ValueError("Unsupported type.")

            if "dict" in item:
                value = item["dict"][int(value)]

            data[name] = value

        return data
