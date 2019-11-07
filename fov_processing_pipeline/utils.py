from numpy.random import Generator, PCG64


def int2rand(id):
    # psuedorandomly deterministically convert an ID (integer) to a random number between 0 and 1
    rg = Generator(PCG64(id))
    return rg.random()
