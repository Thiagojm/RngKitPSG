import time



def main(n):
    print("Num choosen = " + str(n))
    t0 = time.time()
    print("fib num = " + str(fib(n)))
    t1 = time.time()
    print("total time: " + str(t1 - t0))

def fib(n):
    if n < 2:
        return n

    return fib(n-1) + fib(n-2)

main(40)
