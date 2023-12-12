import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import griddata
from cmap import Colormap

import time

mpl.rcParams['animation.ffmpeg_path'] = r'C:\installers\tools\ffmpeg-6.0-essentials_build\bin\ffmpeg.exe'
# mpl.rcParams['animation.ffmpeg_path'] = r'C:\ffmpeg-2023-12-04-git-8c117b75af-full_build\bin\ffmpeg.exe'

def benchmark(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end-start:0.4f} seconds to complete")
        return result
    return wrapper


class TShapePlotter:
    '''
    A class for creating 3D animated visualizations of a T-shaped object.

    Attributes:
        fig (Figure): The matplotlib figure object for the plot.
        ax (Axes3D): The 3D axes object for the plot.
        azim (int): Azimuthal angle for the 3D plot.
        elev (int): Elevation angle for the 3D plot.
    '''
    
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(projection='3d')
    azim = 30
    elev = 20

    def __init__(self, top_len, stem_len, w, pd_dia=5, centers=None, rc=0, isShowStep=False):
        '''
        Initialize the TShapePlotter with dimensions and properties for the T-shape.

        Input:
            top_len [int]: The length of the top part of the T-shape.
            stem_len [int]: The length of the stem part of the T-shape.
            w [int]: The width of the T-shape.
            pd_dia [int]: Diameter of the pressure distribution area. Default is 5.
            centers [list of lists]: Center points for pressure values. Default is None.
            rc [int]: Radius for round corners. Default is 0.
            isShowStep [bool]: Flag to show steps during animation. Default is False.
        """
        '''
        self.top_len = top_len
        self.stem_len = stem_len
        self.w = w
        self.pd_dia = pd_dia
        self.rc = rc

        if centers is None:
            self.centers = [[15, 50], [85, 50], [85, 15], [85, 85]]
        else:
            self.centers = centers

        self.isShowStep = isShowStep

    def _generate_t(self):
        '''
        Generates a grid for the T-shape and applies masks to shape it.
        Internal use only.
        '''

        # Calculate square and corner sizes
        self.frame_w = self.stem_len
        self.frame_h = self.top_len + self.w
        
        x, y = np.meshgrid(np.linspace(-self.frame_w/2, self.frame_w/2, 100), 
                           np.linspace(-self.frame_h/2, self.frame_h/2, 100))
        
        self.t_full = np.column_stack([x.ravel(), y.ravel(), np.zeros_like(x.ravel())])
        
        # Masks for removing bottom corners
        mask_left = np.logical_or(x > -self.w/2, y > self.frame_h/2 - self.w)
        mask_right = np.logical_or(x < self.w/2, y > self.frame_h/2 - self.w)
        mask = np.logical_and(mask_left, mask_right)

        # Masks for removing corners
        if self.rc > 0:
            exclude_masks = [
                np.logical_and(x <= -self.frame_w/2 + self.rc, y >= self.frame_h/2 - self.rc), # ttl
                np.logical_and(x >= self.frame_w/2 - self.rc, y >= self.frame_h/2 - self.rc), # ttr
                np.logical_and(x <= -self.frame_w/2 + self.rc, y <= self.frame_h/2 - self.w + self.rc), # tbl
                np.logical_and(x >= self.frame_w/2 - self.rc, y <= self.frame_h/2 - self.w + self.rc), # tbr
                np.logical_and(x <= -self.w/2 + self.rc, y <= -self.frame_h/2 + self.rc), # vbl
                np.logical_and(x >= self.w/2 - self.rc, y <= -self.frame_h/2 + self.rc) # vbr
            ]

            exclude_combined_mask = np.any(exclude_masks, axis=0)
            mask = np.logical_and(mask, np.logical_not(exclude_combined_mask))

            include_masks = [
                np.sqrt((x - (-self.frame_w/2 + self.rc))**2 + (y - (self.frame_h/2 - self.rc))**2) <= self.rc, # ttl
                np.sqrt((x - (self.frame_w/2 - self.rc))**2 + (y - (self.frame_h/2 - self.rc))**2) <= self.rc, # ttr
                np.sqrt((x - (-self.frame_w/2 + self.rc))**2 + (y - (self.frame_h/2 - self.w + self.rc))**2) <= self.rc, # tbl
                np.sqrt((x - (self.frame_w/2 - self.rc))**2 + (y - (self.frame_h/2 - self.w + self.rc))**2) <= self.rc, # tbr
                np.sqrt((x - (-self.w/2 + self.rc))**2 + (y - (-self.frame_h/2 + self.rc))**2) <= self.rc, # vbl
                np.sqrt((x - (self.w/2 - self.rc))**2 + (y - (-self.frame_h/2 + self.rc))**2) <= self.rc # vbr
            ]
            
            include_combined_mask = np.any(include_masks, axis=0)
            mask = np.logical_or(mask, include_combined_mask)

        self._t_mask = mask

    def _generate_ref_circ(self, diameter, n_ref_points):
        '''
        Generates reference circles in different planes for the 3D visualization.

        Input:
            diameter [int]: Diameter of the reference circles.
            n_ref_points [int]: Number of points to generate for the circles.
        '''

        theta = np.linspace(0, 2*np.pi, n_ref_points)

        # Circle parallel to XY plane
        x_xy = diameter/2 * np.cos(theta)
        y_xy = diameter/2 * np.sin(theta)
        z_xy = np.zeros_like(theta)
        
        # Circle parallel to YZ plane
        x_yz = np.zeros_like(theta)
        y_yz = diameter/2 * np.cos(theta)
        z_yz = diameter/2 * np.sin(theta)
        
        # Circle parallel to ZX plane
        x_zx = diameter/2 * np.cos(theta)
        y_zx = np.zeros_like(theta)
        z_zx = diameter/2 * np.sin(theta)

        self.xy_circle = np.column_stack([x_xy, y_xy, z_xy])
        self.yz_circle = np.column_stack([x_yz, y_yz, z_yz])
        self.zx_circle = np.column_stack([x_zx, y_zx, z_zx])

    def _generate_axes(self, diameter):
        '''
        Creates axis lines for the 3D plot.

        Input:
            diameter [int]: Diameter of the axes.
        '''
        self.x_axes = np.array([[diameter / 2, 0, 0], [-diameter / 2, 0, 0]])
        self.y_axes = np.array([[0, diameter / 2, 0], [0, -diameter / 2, 0]])
        self.z_axes = np.array([[0, 0, diameter / 2], [0, 0, -diameter / 2]])

    def _generate_vals(self):
        '''
        Initializes an array to hold values for displacing the T-shape's surface.
        Internal use only.
        '''
        self.vals = np.zeros([100, 100])

    def _rotate(self, coords):
        '''
        Applies a rotation to the T-shape based on Euler angles.

        Input:
            coords [array-like]: Coordinates to rotate.

        Return:
            [array-like]: Rotated coordinates.
        '''
        # BLE received order: R-P-Y (ZYX)
        # IMU real order: P-R-Y (YZX)
        # body real order: Y-R-P (XZY)
        rotation = R.from_euler('XZY', self.euler_angles, degrees=True)
        return rotation.apply(coords)
    
    def _displacement(self):
        '''
        Adjusts the T-shape's Z-coordinates based on the values array.
        Internal use only.
        '''
        displacement = np.zeros_like(self.vals)
        displacement[self._t_mask] = self.vals[self._t_mask]
        self.t_full[:, 2] = displacement.ravel()

    def _interpolate(self):
        '''
        Performs interpolation for the T-shape's displacement values.
        Internal use only.
        '''
        known_points = np.column_stack(np.where(np.logical_or(self._known_mask,
                                                              np.isin(np.arange(100), [0, 99])[:, None] |
                                                              np.isin(np.arange(100), [0, 99])[None, :])))
        known_values = self.vals[known_points[:, 0], known_points[:, 1]]

        # Generate grid for the entire array
        grid_x, grid_y = np.mgrid[0:99:100j, 0:99:100j]

        # Interpolate values for the entire grid
        self.vals = griddata(known_points, known_values, (grid_x, grid_y),
                             method='cubic', fill_value=0)
        
    def set_pv(self, pvs):
        all_pv_masks = np.zeros_like(self.vals, dtype=bool)
        for i, center in enumerate(self.centers):
            y, x = np.ogrid[-center[0]:100-center[0], -center[1]:100-center[1]]
            pv_mask = x*x + y*y <= (self.pd_dia/2)**2
            self.vals[pv_mask] = pvs[i]

            all_pv_masks = np.logical_or(all_pv_masks, pv_mask)
        self._known_mask = all_pv_masks
        self._interpolate()

    def set_angles(self, angles):
        self.euler_angles = angles

    def init_canvas(self, ref_diameter=1.5, n_ref_points=500):
        self._generate_t()
        self._generate_ref_circ(ref_diameter*max(self.frame_h, self.frame_w), n_ref_points)
        self._generate_axes(ref_diameter*max(self.frame_h, self.frame_w))
        self._generate_vals()
        
        self.ax.view_init(elev=self.elev, azim=self.azim)
        self.ax.set_proj_type('ortho')
        # self.ax.text('t = 0.0s')

        self.ax.set_xlim([-4, 4])
        self.ax.set_ylim([-4, 4])
        self.ax.set_zlim([-4, 4])

        self.ax.set_box_aspect((1, 1, 1))
        self.ax.grid(False)
        self.ax.axis('off')

        if not hasattr(self, 't_scatter'):
            self.t_scatter = self.ax.scatter(self.t_full[self._t_mask.ravel()][:, 0],
                                            self.t_full[self._t_mask.ravel()][:, 1],
                                            self.t_full[self._t_mask.ravel()][:, 2],
                                            c=self.vals[self._t_mask], s=1,
                                            cmap=Colormap('cmocean:balance').to_matplotlib(),
                                            vmax=1, vmin=0,
                                            alpha=1)
            self.xy_line,  = self.ax.plot(self.xy_circle[:, 0], self.xy_circle[:, 1], self.xy_circle[:, 2],
                                        c='#FF66D0', label='XY Circle', alpha=1)
            self.yz_line,  = self.ax.plot(self.yz_circle[:, 0], self.yz_circle[:, 1], self.yz_circle[:, 2],
                                        c='#909090', label='YZ Circle', alpha=1)
            self.zx_line,  = self.ax.plot(self.zx_circle[:, 0], self.zx_circle[:, 1], self.zx_circle[:, 2],
                                        c='#CA82B0', label='ZX Circle', alpha=1)
            self.x_line,   = self.ax.plot(self.x_axes[:, 0], self.x_axes[:, 1], self.x_axes[:, 2],
                                        c='silver', ls='--')
            self.y_line,   = self.ax.plot(self.y_axes[:, 0], self.y_axes[:, 1], self.y_axes[:, 2],
                                        c='silver', ls='--')
            self.z_line,   = self.ax.plot(self.z_axes[:, 0], self.z_axes[:, 1], self.z_axes[:, 2],
                                        c='silver', ls='--')

    def draw(self):
        # Add displacement
        self._displacement()

        # Rotate everything
        self.t_rot_full = self._rotate(self.t_full)
        # mask_rot = self._rotate(self._t_mask)

        self.xy_rot = self._rotate(self.xy_circle)
        self.yz_rot = self._rotate(self.yz_circle)
        self.zx_rot = self._rotate(self.zx_circle)

        self.x_axes_rot = self._rotate(self.x_axes)
        self.y_axes_rot = self._rotate(self.y_axes)
        self.z_axes_rot = self._rotate(self.z_axes)
        
        # Plot the T-shape
        self.t_scatter._offsets3d = (self.t_rot_full[self._t_mask.ravel()][:, 0],
                                     self.t_rot_full[self._t_mask.ravel()][:, 1],
                                     self.t_rot_full[self._t_mask.ravel()][:, 2])
        self.t_scatter.set_array(self.vals[self._t_mask])
        
        # Plot the circles
        self.xy_line.set_data_3d(self.xy_rot[:, 0], self.xy_rot[:, 1], self.xy_rot[:, 2])
        self.yz_line.set_data_3d(self.yz_rot[:, 0], self.yz_rot[:, 1], self.yz_rot[:, 2])
        self.zx_line.set_data_3d(self.zx_rot[:, 0], self.zx_rot[:, 1], self.zx_rot[:, 2])
        
        # Plot the axes
        self.x_line.set_data_3d(self.x_axes_rot[:, 0], self.x_axes_rot[:, 1], self.x_axes_rot[:, 2])
        self.y_line.set_data_3d(self.y_axes_rot[:, 0], self.y_axes_rot[:, 1], self.y_axes_rot[:, 2])
        self.z_line.set_data_3d(self.z_axes_rot[:, 0], self.z_axes_rot[:, 1], self.z_axes_rot[:, 2])

    def show(self):
        plt.show()

    def set_data(self, pvs, angles):
        self.pvs_data = pvs
        self.angles_data = angles
    
    def update_ani(self, frame):
        self.set_pv(self.pvs_data[frame])
        self.set_angles(self.angles_data[frame])
        if self.isShowStep and frame % 100 == 0:
            print(f'Generating frame {frame}, overall {len(self.pvs_data)} frames.')
        self.draw()

    def animate(self):
        '''
        Creates and displays the animation.
        '''
        self.init_canvas()
        self.anim = animation.FuncAnimation(self.fig, self.update_ani, interval=1,
                                            frames=len(self.pvs_data), repeat=False)
        plt.show()

# Read data
def main():
    '''
    Main function to read data, initialize TShapePlotter, set data, and generate animation.
    '''
    data = np.loadtxt('interp_data.csv', delimiter=',') # the angle data uses the sequence "roll, pitch, yaw"
    pvs_array = data[:, 2:6]
    angles_array = data[:, 6:9]
    angles_array[:, 1] += 180
    angles_array[:, 2] += 90

    # plt.figure()
    # plt.plot(angles_array)

    plotter = TShapePlotter(4, 6, 2, pd_dia=10, rc=1, isShowStep=True)
    plotter.azim = 40
    plotter.elev = 30

    # Generate animation
    plotter.set_data(pvs_array, angles_array)
    # plotter.init_canvas()
    plotter.animate()

    ffwriter = animation.FFMpegWriter(fps=60)
    plotter.anim.save('interp_data.mp4', writer=ffwriter)
    
if __name__ == '__main__':
    main()