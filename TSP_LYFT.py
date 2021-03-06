import math
import random
import lyft_function
import json
def distL2((x1,y1), (x2,y2)):
    """Compute the L2-norm (Euclidean) distance between two points.

    The distance is rounded to the closest integer, for compatibility
    with the TSPLIB convention.

    The two points are located on coordinates (x1,y1) and (x2,y2),
    sent as parameters"""
    #print "x1="+str(x1)+" y1="+str(y1)+" x2="+str(x2)+" y2="+str(y2)
    ans = json.loads(lyft_function.given_cost([x1,y1],[x2,y2]))

    return ans['cost']
def final_result(coord, tour_list):

    print "Calculating the final result............"
    n = len(tour_list)
    total_costs_by_cheapest_car_type = 0
    total_duration = 0
    total_distance = 0
    result = {}
    result['distance_unit'] = 'mile'
    result['duration_unit'] = 'minute'
    result['current_code'] = 'USD'
    result['name'] = 'Lyft'
    result['total_costs_by_cheapest_car_type'] = 0
    result['total_duration'] = 0
    result['total_distance'] = 0

    for i in range(0, n-1):
        ans = json.loads(lyft_function.given_cost(coord[tour_list[i]],coord[tour_list[i+1]]))
        #print "=====" + str(i)+str(i+1) + "====="
        #print (coord[tour_list[i]][0],coord[tour_list[i]][1])
        #print (coord[tour_list[i+1]][0],coord[tour_list[i+1]][1])
        #print ans
        result['total_costs_by_cheapest_car_type'] += ans['cost']
        result['total_duration'] += ans['duration']
        result['total_distance'] += ans['distance']

    print "Finish calculating the final result"
    return result   

def distL1((x1,y1), (x2,y2)):
    """Compute the L1-norm (Manhattan) distance between two points.

    The distance is rounded to the closest integer, for compatibility
    with the TSPLIB convention.

    The two points are located on coordinates (x1,y1) and (x2,y2),
    sent as parameters"""
    return int(abs(x2-x1) + abs(y2-y1)+.5)


def mk_matrix(coord, dist):
    """Compute a distance matrix for a set of points.

    Uses function 'dist' to calculate distance between
    any two points.  Parameters:
    -coord -- list of tuples with coordinates of all points, [(x1,y1),...,(xn,yn)]
    -dist -- distance function
    """
    n = len(coord)
    D = {}      # dictionary to hold n times n matrix
    for i in range(n-1):
        for j in range(i+1,n):
            (x1,y1) = coord[i]
            (x2,y2) = coord[j]

            # D[i,j] = dist((x1,y1), (x2,y2))
            # D[j,i] = D[i,j]
            if((i == 0 and j == n-1)):
                D[i,j] = 9000000
                D[j,i] = 0
            else:
                D[i,j] = dist((x1,y1), (x2,y2))
                D[j,i] = D[i,j]
                

            # if(i != 0 and j != n-1):
            #     D[j,i] = D[i,j]
            # else:
            #     D[j,i] = 9000000


    return n,D

def read_tsplib(filename):
    "basic function for reading a TSP problem on the TSPLIB format"
    "NOTE: only works for 2D euclidean or manhattan distances"
    f = open(filename, 'r');

    line = f.readline()
    while line.find("EDGE_WEIGHT_TYPE") == -1:
        line = f.readline()

    if line.find("EUC_2D") != -1:
        dist = distL2
    elif line.find("MAN_2D") != -1:
        dist = distL1
    else:
        print "cannot deal with non-euclidean or non-manhattan distances"
        raise Exception

    while line.find("NODE_COORD_SECTION") == -1:
        line = f.readline()

    xy_positions = []
    while 1:
        line = f.readline()
        if line.find("EOF") != -1: break
        (i,x,y) = line.split()
        x = float(x)
        y = float(y)
        xy_positions.append((x,y))

    n,D = mk_matrix(xy_positions, dist)
    return n, xy_positions, D


def mk_closest(D, n):
    """Compute a sorted list of the distances for each of the nodes.

    For each node, the entry is in the form [(d1,i1), (d2,i2), ...]
    where each tuple is a pair (distance,node).
    """
    C = []
    for i in range(n):
        dlist = [(D[i,j], j) for j in range(n) if j != i]
        dlist.sort()
        C.append(dlist)
    return C


def length(tour, D):
    """Calculate the length of a tour according to distance matrix 'D'."""
    z = D[tour[-1], tour[0]]    # edge from last to first city of the tour
    for i in range(1,len(tour)):
        z += D[tour[i], tour[i-1]]      # add length of edge from city i-1 to i
    return z


def randtour(n):
    """Construct a random tour of size 'n'."""
    sol = range(1,n-1)      # set solution equal to [0,1,...,n-1]
    random.shuffle(sol) # place it in a random order
    #print sol
    ls = [0]


    #print ls + sol + [n-1]
    return ls + sol + [n-1]


def nearest(last, unvisited, D):
    """Return the index of the node which is closest to 'last'."""
    near = unvisited[0]
    min_dist = D[last, near]
    for i in unvisited[1:]:
        if D[last,i] < min_dist:
            near = i
            min_dist = D[last, near]
    return near


def nearest_neighbor(n, i, D):
    """Return tour starting from city 'i', using the Nearest Neighbor.

    Uses the Nearest Neighbor heuristic to construct a solution:
    - start visiting city i
    - while there are unvisited cities, follow to the closest one
    - return to city i
    """
    unvisited = range(n-1)
    unvisited.remove(i)
    last = i
    tour = [i]
    while unvisited != []:
        next = nearest(last, unvisited, D)
        tour.append(next)
        unvisited.remove(next)
        last = next
    tour.append(n-1)
    return tour



def exchange_cost(tour, i, j, D):
    """Calculate the cost of exchanging two arcs in a tour.

    Determine the variation in the tour length if
    arcs (i,i+1) and (j,j+1) are removed,
    and replaced by (i,j) and (i+1,j+1)
    (note the exception for the last arc).

    Parameters:
    -t -- a tour
    -i -- position of the first arc
    -j>i -- position of the second arc
    """
    n = len(tour)
    a,b = tour[i],tour[(i+1)%n]
    c,d = tour[j],tour[(j+1)%n]
    return (D[a,c] + D[b,d]) - (D[a,b] + D[c,d])


def exchange(tour, tinv, i, j):
    """Exchange arcs (i,i+1) and (j,j+1) with (i,j) and (i+1,j+1).

    For the given tour 't', remove the arcs (i,i+1) and (j,j+1) and
    insert (i,j) and (i+1,j+1).

    This is done by inverting the sublist of cities between i and j.
    """
    #print str(i)+" "+str(j)
    n = len(tour)
    #if i>j and i != 0 and i != n-1:
    if i>j:
        i,j = j,i
    #print str(i)+" "+str(j)
    assert i>=0 and i<j-1 and j<n
    path = tour[i+1:j+1]
    path.reverse()
    tour[i+1:j+1] = path
    for k in range(i+1,j+1):
        tinv[tour[k]] = k


def improve(tour, z, D, C):
    """Try to improve tour 't' by exchanging arcs; return improved tour length.

    If possible, make a series of local improvements on the solution 'tour',
    using a breadth first strategy, until reaching a local optimum.
    """
    n = len(tour)
    tinv = [0 for i in tour]
    for k in range(n):
        tinv[tour[k]] = k  # position of each city in 't'
    for i in range(1,n-2):
        a,b = tour[i],tour[(i)%(n-2)+1]
        #print "i="+str(i)+" n="+str(n)+" a="+str(i) + " b="+str((i)%(n-2)+1)

        dist_ab = D[a,b]
        improved = False
        for dist_ac,c in C[a]:
            if dist_ac >= dist_ab:
                break
            j = tinv[c]
            d = tour[(j+1)%n]
            dist_cd = D[c,d]
            dist_bd = D[b,d]
            delta = (dist_ac + dist_bd) - (dist_ab + dist_cd)
            if delta < 0 and i != 0 and j !=n-1:       # exchange decreases length
                exchange(tour, tinv, i, j);
                z += delta
                improved = True
                break
        if improved:
            continue
        for dist_bd,d in C[b]:
            if dist_bd >= dist_ab:
                break
            j = tinv[d]-1
            if j==-1:
                j=n-1
            c = tour[j]
            dist_cd = D[c,d]
            dist_ac = D[a,c]
            delta = (dist_ac + dist_bd) - (dist_ab + dist_cd)
            if delta < 0 and i != 0 and j !=n-1:       # exchange decreases length
                exchange(tour, tinv, i, j);
                z += delta
                break
    return z


def localsearch(tour, z, D, C=None):
    """Obtain a local optimum starting from solution t; return solution length.

    Parameters:
      tour -- initial tour
      z -- length of the initial tour
      D -- distance matrix
    """
    n = len(tour)
    if C == None:
        C = mk_closest(D, n)     # create a sorted list of distances to each node
    while 1:
        newz = improve(tour, z, D, C)
        if newz < z:
            z = newz
        else:
            break
    return z


def multistart_localsearch(k, n, D, report=None):
    """Do k iterations of local search, starting from random solutions.

    Parameters:
    -k -- number of iterations
    -D -- distance matrix
    -report -- if not None, call it to print verbose output

    Returns best solution and its cost.
    """
    C = mk_closest(D, n) # create a sorted list of distances to each node
    bestt=None
    bestz=None
    for i in range(0,k):
        tour = randtour(n)
        z = length(tour, D)
        z = localsearch(tour, z, D, C)
        if z < bestz or bestz == None:
            bestz = z
            bestt = list(tour)
            if report:
                report(z, tour)

    return bestt, bestz


def run_lyft(input_coord):
    """Local search for the Travelling Saleman Problem: sample usage."""

    #
    # test the functions:
    #

    # random.seed(1)    # uncomment for having always the same behavior
    import sys
    if len(sys.argv) == 1:
        # create a graph with several cities' coordinates
        #coord = [(4,0),(5,6),(8,3),(4,4),(4,1),(4,3),(2,7),(6,8),(3,1)]


        #coord = [(37.71,-122.41),(37.72,-122.41),(37.75,-122.41),(37.79,-122.41)]
        coord = input_coord

        n, D = mk_matrix(coord, distL2) # create the distance matrix
        instance = "toy problem"
    else:
        instance = sys.argv[1]
        n, coord, D = read_tsplib(instance)     # create the distance matrix
        # n, coord, D = read_tsplib('INSTANCES/TSP/eil51.tsp')  # create the distance matrix

    # function for printing best found solution when it is found
    from time import clock
    init = clock()
    def report_sol(obj, s=""):
        print "cpu:%g\tobj:%g\ttour:%s" % \
              (clock(), obj, s)


    #print "*** travelling salesman problem ***"
    #print

    # # random construction
    # print "random construction + local search:"
    # tour = randtour(n)     # create a random tour
    # z = length(tour, D)     # calculate its length
    # print "random:", tour, z, '  -->  ',
    # z = localsearch(tour, z, D)      # local search starting from the random tour
    # print tour, z
    # print

    # # greedy construction
    # print "greedy construction with nearest neighbor + local search:"
    # #for i in range(n):
    # for i in range(1):
    #     tour = nearest_neighbor(n, i, D)     # create a greedy tour, visiting city 'i' first
    #     z = length(tour, D)
    #     print "nneigh:", tour, z, '  -->  ',
    #     z = localsearch(tour, z, D)
    #     print tour, z
    # print

    # multi-start local search
    #print "random start local search:"
    niter = 30
    tour,z = multistart_localsearch(niter, n, D, report_sol)
    #assert z == length(tour, D)
    print "best found solution (%d iterations): z = %g" % (niter, z)
    print tour

    
    return (final_result(coord, tour), tour)
