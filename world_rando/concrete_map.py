# Creates a concrete map based on an abstract map
# a map is a data structure:
# key1 - area (ex. "Maridia")
# key2 - (x,y) tuple
# value - MapTile
import collections
import heapq
import random

class MCoords(object):
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return MCoords(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return MCoords(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return MCoords(self.x * other.x, self.y * other.y)

    def up(self):
        return MCoords(self.x, self.y - 1)

    def right(self):
        return MCoords(self.x + 1, self.y)

    def down(self):
        return MCoords(self.x, self.y + 1)

    def left(self):
        return MCoords(self.x - 1, self.y)

    def neighbors(self):
        return self.left(), self.up(), self.right(), self.down()

    def to_tuple(self):
        return (self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash(self.to_tuple())

    def euclidean(self, other):
        return ((self.x-other.x)**2 + (self.y-other.y)**2)**(0.5)

    def __repr__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"
        

class MapTile(object):

    def __init__(self, mtype):
        self.t = mtype
        # key - MCoords
        # value - itemset needed to reach
        self.d = collections.defaultdict(list)
        # list of MCoords adjacent to this tile indicating where the walls are
        self.walls = set() #TODO: what about sloped map tiles? #TODO: walls as a set
        self.is_item = False
        self.is_elevator = False
        self.is_e_tile = False
        self.is_fixed = False

    def add_path(to_coords, with_items):
        self.d[to_coords].append(with_items)

def map_extent(rcmap):
    """ returns the 'extent' of the cmap: two 
    mcoords, which are the bounding box"""
    mtiles = rcmap.keys()
    if len(mtiles) == 0:
        return None
    minx = min(mtiles, key=lambda item: item.x).x
    miny = min(mtiles, key=lambda item: item.y).y
    maxx = max(mtiles, key=lambda item: item.x).x
    maxy = max(mtiles, key=lambda item: item.y).y
    return (MCoords(minx, miny), MCoords(maxx, maxy))

def map_range(rcmap):
    """Returns the actual ranges of the map, along with the placement of that range in x,y"""
    mmin, mmax = map_extent(rcmap)
    return mmax - mmin, mmin

def map_offset(cmap, offset):
    """Returns a new cmap which is the same as the old cmap at a different offset. Data may be shared."""
    offset_map = {m + offset : mtile for m, mtile in cmap.items()}
    # offset the walls
    for t in offset_map.values():
        t.walls = set([i + offset for i in t.walls])
    return offset_map

def add_cmaps(cmap1, cmap2, collision_policy):
    """Puts cmap1 and cmap2 together. Data may be shared."""
    new_cmap = {}
    for c, t in cmap1.items():
        new_cmap[c] = t
    for c, t in cmap2.items():
        if c in new_cmap:
            if collision_policy == "f":
                continue
            elif collision_policy == "e":
                assert False, "cmap collision: " + str(c)
            elif collision_policy == "n":
                return None
            else:
                assert False, "Bad collision policy"
        else:
            new_cmap[c] = t
    return new_cmap

def euclidean(p1, p2):
    """euclidean metric"""
    return p1.euclidean(p2)

def manhattan(p1, p2):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

def rand_d(p1, p2):
    return euclidean(p1, p2) + random.uniform(0,9)

#TODO: some optimizations can be made
# note that dist can be random, in which case this is kind of a random walk that
# 'eventually' reaches q
#TODO: optional "timeout" argument that makes sure that
#   a. the random walk will terminate
#   b. it won't just take forever when you don't give it a pred
def map_search(start, goal, pred=lambda x: True, dist=lambda x,y: euclidean(x,y)):
    """search to find the path from start to goal, under tiles satisfying pred
    placing new tiles into the queue by sorting them over the metric dist."""
    
    h = []
    finished = set()
    offers = {}
    heapq.heappush(h, (0, start))
    finished.add(start)
    while len(h) > 0:
        _, pos = heapq.heappop(h)
        if pos == goal:
            return offers, finished
        for a in pos.neighbors():
            if a not in finished and pred(a):
                heapq.heappush(h, (dist(a, goal), a))
                finished.add(a)
                offers[a] = pos
    # not found
    return None

def map_bfs(start, goal, pred=lambda x: True):
    """bfs over nodes satisfying pred. If goal is None, just returns all there was to see."""
    #TODO: what to do if there's no pred and no goal?
    q = collections.deque([start])
    finished = set()
    offers = {}
    finished.add(start)
    while len(q) > 0:
        pos = q.popleft()
        if goal is not None and pos == goal:
            return offers, finished
        n = pos.neighbors()
        for a in n:
            if a not in finished and pred(a):
                q.append(a)
                finished.add(a)
                offers[a] = pos
    return offers, finished

#TODO
def map_lsearch(start, goal, pred=lambda x:True, dist=lambda x,y: euclidean(x,y)):
    """special search that first finds failure states in moving from start to goal,
    then moves only towards the goal to reach it, minimizing dist at each step.
    The goal here is that we can generate random, but more 'straight' paths than a random
    walk will do."""
    diff = goal - start
    pass

def get_path(offers, start, end):
    if end not in offers:
        return None
    pos = end
    path = []
    while True:
        path.append(pos)
        if pos == start:
            break
        pos = offers[pos]
    return path[::-1]

def elide_walls(cmap):
    """ adds walls to cmap where the tile abuts empty space """
    for xy in cmap.keys():
        n = xy.neighbors()
        for a in n:
            if a not in cmap:
                cmap[xy].walls.add(a)

#lambda x: 0 means BFS in a heapq (first element first)
# can use random to alter the pattern of vertices grabbed by
# each mean
def bfs_partition(space, means, priority=lambda x: 0):
    # setup
    # key - mean, value - set of positions that mean has considered
    mfinished = {mean: set() for mean in means}
    # key - mean, value - for position p, what made the a* offer to p?
    moffers = {mean: {} for mean in means}
    for mean in means:
        mfinished[mean].add(mean)
    mpos = {mean: mean for mean in means}
    mheaps = {mean: [(0, mean)] for mean in means}
    all_finished = set(means)
    while all_finished != space:
        for mean in means:
            if len(mheaps[mean]) > 0:
                _, mpos[mean] = heapq.heappop(mheaps[mean])
            else:
                continue
            for n in mpos[mean].neighbors():
                if n not in all_finished and n in space:
                    heapq.heappush(mheaps[mean], (priority(n), n))
                    mfinished[mean].add(n)
                    all_finished.add(n)
                    moffers[mean][n] = mpos[mean]
    return moffers, mfinished

def random_rooms(n, rcmap):
    # choose means
    means = random.sample(rcmap.keys(), n)
    paths, partitions = bfs_partition(set(rcmap.keys()), means)
    for mean in means:
        room_walls(rcmap, partitions[mean])
    return paths, partitions

def room_walls(rcmap, room):
    """ puts the walls into a room, given as a set of MCoords """
    for xy in room:
        for n in xy.neighbors():
            if n not in room:
                rcmap[xy].walls.add(n)

###
# SPECIFY MAP TILES
# ways to specify a set of map tiles to search with map_search (using pred)
###

def is_above(xy1, xy2):
    return xy1.x == xy2.x and xy1.y < xy2.y

def is_below(xy1, xy2):
    return xy1.x == xy2.x and xy1.y > xy2.y

def is_p_list(xy1, xys, p):
    """does xy1 satisfy p with any element of xys?"""
    for xy2 in xys:
        if p(xy1, xy2):
            return True
    return False

def is_below_l(xy1, xys):
    return is_p_list(xy1, xys, is_below)

def is_above_l(xy1, xys):
    return is_p_list(xy1, xys, is_above)
