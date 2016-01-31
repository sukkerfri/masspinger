__author__ = 'sukkerfri'

import argparse
import colorama
import os
import subprocess
import sys
import threading
import queue

MAXTHREADS = 32
PINGCOMMAND = ['ping.exe',
                   '-n', '1',       # send one ping
                   '-f',            # No fragmentation
                   '-w', '1500',    # timeout in milliseconds
                   ]


# hack to make print() thread safe
# http://bramcohen.livejournal.com/70686.html
mylock = threading.Lock()
p = print
def print(*a, **b):
    with mylock:
        p(*a, **b)


class Host:
    def __init__(self, host):
        self.host = host
        self.pingcommand = PINGCOMMAND + [host]
        self.ping_returncode = None
        return


def worker(q, list):
    if args.verbose:
            print("Spawning {0}".format(threading.currentThread().getName()))
    while not q.empty():
        host = q.get()
        with open(os.devnull, 'w') as nul:
            # Ping the computer
            host.ping_returncode = subprocess.call(host.pingcommand, stdout=nul, stderr=nul)
            if host.ping_returncode == 0:
                print(colorama.Fore.GREEN + host.host)
            elif args.verbose:
                print(colorama.Fore.RED + host.host)
        list.append(host)
        q.task_done()
    if args.verbose:
            print("Terminating {0}".format(threading.currentThread().getName()))



def startworkers(queue, nthreads):
    finished = []
    for i in range(nthreads):
        t = threading.Thread(name="Thread #{0}".format(i + 1), target=worker, args=(queue, finished), daemon=False)
        t.start()
    queue.join()
    return finished


if __name__ == "__main__":
    # https://pypi.python.org/pypi/colorama
    colorama.init(autoreset=True)

    # https://docs.python.org/3/howto/argparse.html
    parser = argparse.ArgumentParser(description="Pings lots of hosts very fast.")


    parser.add_argument("hosts", nargs="*", help="Host(s) to ping", type=str, default="", metavar="host")
    parser.add_argument("-f", "--file", help="Textfile with hostnames, one per line")

    parser.add_argument("-m", "--maxthreads", type=int, help="Maximum no. of threads to spawn simultaniously. Default is {}".format(MAXTHREADS), metavar="THREADS", default=MAXTHREADS)
    parser.add_argument("-v", "--verbose", help="Increase verbosity", action="store_true")

    args = parser.parse_args()
    q = queue.Queue()

    if not args.hosts == "":
        for h in args.hosts:
            q.put(Host(h))

    if args.file and os.path.isfile(args.file):
        with open(args.file, "r") as f:
            for line in f:
                if len(line) > 0:
                    q.put(Host(line.strip()))

    queuesize = q.qsize()
    if queuesize:
        threads = args.maxthreads if args.maxthreads <= queuesize else queuesize
        results = startworkers(q, threads)
        if args.verbose:
            print("Processed {0} host(s)".format(len(results)))
            print("Replies: {0}".format(len([x for x in results if x.ping_returncode == 0])))
    else:
        parser.print_help()
        sys.exit(1)