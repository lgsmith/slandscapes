import numpy as np
from . import landscape
from scipy.ndimage import gaussian_filter


def funneled_landscape(grid_size, width_frac=0.707, depth=1, resolution=1):
    l = landscape(grid_size=grid_size, resolution=resolution)
    x0 = np.array([grid_size[0], grid_size[1]])
    widths = x0*width_frac
    l = l.add_gaussian(x0, height=-depth, widths=widths)
    return l


def diagonal_barrier(
        grid_size, position=0.5, height=1, width=1, resolution=1):
    l = landscape(grid_size=grid_size, resolution=resolution)
    semi_circum = len(l.x1_coords)+len(l.x1_coords[0]) - 1
    diag = int(semi_circum * position) - len(l.x1_coords)
    centers = np.array(
        list(
            zip(
                l.x1_coords[::-1].diagonal(diag),
                l.x2_coords[::-1].diagonal(diag))))
    for center in centers:
        l = l.add_gaussian(x0s=center, height=height, widths=width)
    return l


def egg_carton_landscape(
        grid_size, gaussians_per_axis, height=1, width=1, resolution=1):
    l = landscape(grid_size=grid_size, resolution=resolution)
    l = l.add_noise(
        gaussians_per_axis=gaussians_per_axis, height_range=[height, height],
        width_range=[width, width], rigidity=100000)
    return l


def slant_landscape(
        grid_size, gradient=1.0, resolution=1):
    l = landscape(grid_size=grid_size, resolution=resolution)
    l.values = np.array(
        [np.arange(l.values.shape[1]) * gradient] * l.values.shape[0])
    return l

def single_barrier(grid_x=40,grid_y=20,barrier_height=3,add_noise=False):
    l = landscape((grid_x,grid_y))
    x_col = int(grid_x / 2)
    l.values[:,x_col] = barrier_height
    if add_noise:
        l = l.add_noise(gaussians_per_axis=10, height_range=[-(barrier_height/2),(barrier_height/2)])
    return l

def multiple_paths(grid_x=40,path_width=5,barrier_height=3,add_noise=False,number_paths=3):
    grid_y = (path_width * number_paths) + (number_paths - 1)
    l = landscape((grid_x,grid_y))
    barrier_list = [path_width]
    x_col = int(grid_x/5)
    for i in range(2,number_paths):
        barrier_list.append((path_width*i) + (i-1))
    l.values[barrier_list,x_col:] = barrier_height
    if add_noise:
        l = l.add_noise(height_range=[-(barrier_height*(1/2)),(barrier_height*(1/2))])
    return l

def multiple_barriers(well_width=100,well_depth=50,barrier_height=3,add_noise=False,number_barriers=3):
    barrier_blocks = ((number_barriers * 2) + 1)
    grid_x = int(well_depth * barrier_blocks)
    grid_y = int(well_width * (5/4))
    l = landscape((grid_x,grid_y))
    j = 1
    for i in range(2,barrier_blocks,2):
        if (j % 2 == 1):
            l.values[-1,((i-1)*well_depth):((i-1)*well_depth + well_depth -1)] = barrier_height
            l.values[int((well_width/4)),((i-1)*well_depth):((i-1)*well_depth + well_depth -1)] = barrier_height
            l.values[int((well_width/4)):-1,((i-1)*well_depth + well_depth -1)] =  barrier_height
        else:
            l.values[0,((i-1)*well_depth):((i-1)*well_depth + well_depth -1)] = barrier_height
            l.values[well_width-1,((i-1)*well_depth):((i-1)*well_depth + well_depth -1)] = barrier_height
            l.values[0:well_width,((i-1)*well_depth + well_depth -1)] =  barrier_height
        j = j+1
    if add_noise:
        l = l.add_noise(height_range=[-(barrier_height*(1/2)),(barrier_height*(1/2))])
    return l

def rugged_landscape(grid_size=(100,30),
                     noise=True,
                     funneled=False,
                     backtrack=False,
                     diagonals=False,
                     b_height=20,
                     b_width=2,
                     b_length=1,
                     instructions={'rand':5}):
    x_dim = grid_size[0]
    y_dim = grid_size[1]
    l = landscape(grid_size)
    if noise:
        l = l.add_noise(gaussians_per_axis=int(0.5*y_dim),height_range=[0.5,0.5],width_range=[-2,2])
    if funneled:
        l = l.add_gaussian(np.array([0,y_dim/2]),height=3.5,widths=np.array([30,50]))
    #Add in barriers
    for key in instructions.keys():
        #User specified location and barrier
        if type(key) is tuple:
            start = key
            for line in instructions[key]:
                height, width, dist, angle = line
                #Add line segment and return new starting position
                start = l.add_barrier(height=height,width=width,start=start,dist=dist,angle=angle)
        #user specified barrier, random location
        elif key == "rand_loc":
            for barrier in instructions[key]:
                x = np.random.randint(x_dim)
                y = np.random.randint(y_dim)
                start = [y,x]
                for line in barrier:
                    heigth, width, dist, angle = line
                    start = l.add_barrier(height=height,width=width,start=start,dist=dist,angle=angle)
        #randomly generated barriers at random locations
        elif key == 'random':
            #Distribution to draw barrier segment lengths from
            mu_d = (np.min(grid_size) / 3) * b_length
            sig_d = (np.min(grid_size) / 5) * b_length
            num_barrs = instructions[key]
            all_barrs = []
            x_spacing = x_dim / num_barrs
            for b in range(num_barrs):
                y = np.random.randint(y_dim)
                x = np.random.randint(b*(x_spacing),(b+1)*(x_spacing)) #along x-axis
                start = [y,x]
                #height = np.random.normal(b_height,1,1)[0]
                #width = np.random.normal(b_width,1,1)[0]
                dist = np.random.normal(mu_d,sig_d, 1)[0]
                if diagonals:
                    angle = np.random.randint(360)
                else:
                    angle = np.random.choice([0,90,180,270])
                if backtrack and np.random.random(1)[0] > 0.95:
                    # make the barrier long enough to definitely reach edge
                    dist = y_dim
                    if start[0] <= (y_dim / 2):
                        angle = np.random.randint(40,70)
                        print(angle,start)
                    else:
                        angle = np.random.randint(290,320)
                        print(angle,start)
                points = l.add_barrier(height=b_height,width=b_width,start=start,dist=dist,angle=angle,draw=False)
                all_barrs.append(points)
            uniq_barrs = np.unique(np.concatenate(all_barrs),axis=0)
            for p in uniq_barrs:
                l.values[p[0],p[1]] = b_height
    return l

def random_gaussian_landscape(
        grid_size=(100, 30),
        n_peaks=100,
        overlapping=True,
        sigma=(1, 1),
        resolution=1,
        gau_scale=1,
        order=0  # pass through to gaussian_filter. number indicates deriv order
):
    l = landscape(grid_size=grid_size,resolution=resolution)
    # randomly scatter gaussians across grid.
    # from https://stackoverflow.com/questions/51545745/numpy-generating-a-2d-sum-of-gaussians-pdf-as-an-array
    impulses = np.zeros_like(l.values)
    if overlapping:
        rows, cols = np.unravel_index(
            np.random.choice(
                impulses.size,
                replace=True,
                size=n_peaks),
            impulses.shape)
        np.add.at(impulses, (rows, cols), 1)
    else:
        rows, cols = np.unravel_index(
            np.random.choice(
                impulses.size,
                replace=False,
                size=n_peaks),
            impulses.shape)
        impulses[rows, cols] = 1
    l.values = gaussian_filter(impulses, sigma, mode='nearest', order=order) * gau_scale
    return l
