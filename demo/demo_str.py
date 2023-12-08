def outer_function():
    yield 1
    yield 2

    def inner_function():
        yield 'a'
        yield 'b'

    inner_gen = inner_function()
    yield from inner_gen

    yield 3

gen = outer_function()
for value in gen:
    print(value)
