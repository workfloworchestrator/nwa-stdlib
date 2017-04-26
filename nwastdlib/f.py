def identity(x):
    return x


def compose(f, g):
    '''
    Get the composition f of g

    >>> compose(fst, list)({2,3,4})
    2
    '''
    return lambda x: f(g(x))
