import random


def probability(p):
    return random.random() <= p


def generate_bin(n):
#    print([random.randint(0, 1) for x in range(n)])
#    print([random.randint(0, 1)] + [1, 1, 1] + [7 * [1, 1, 1, 1, 1, 1]])
#    exit(0)
    # return [random.randint(0, 1) for x in range(n)]
    r = random.randint(0, 2)

    if r == 0:
        return [random.randint(0, 1)] + [1, 1, 1] + (7 * [1, 0, 0, 0, 0, 0])
    elif r == 1:
        return [random.randint(0, 1)] + [1, 0, 0] + (7 * [1, 0, 0, 0, 0, 0])
    else:
        return [random.randint(0, 1)] + [0, 0, 1] + (7 * [0, 1, 0, 0, 0, 0])


def crossover(a, b):
    assert(len(a) == len(b))
    x = random.choice(range(len(a)))
    return a[:x] + b[x:], b[:x] + a[x:]


def mutate_bin(a, p=0.01):
    if probability(p):
        a = list(a)
        x = random.choice(range(len(a)))
        a[x] = 0 if a[x] else 1

    return a


def decode_bin(x, base=1.0):
    xs = "".join(map(str, x))
    v = float(int(xs, 2))

    if base is None:
        return v
    else:
        max = float(pow(2, len(x))-1)
        return (v/max)*base


def decode_dict(genes, choices):
    return choices[int(decode_bin(genes, base=None))]
