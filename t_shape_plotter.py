import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import griddata
from cmap import Colormap

mpl.rcParams['animation.ffmpeg_path'] ='C:\\installers\\tools\\ffmpeg-6.0-essentials_build\\bin\\ffmpeg.exe'

class TShapePlotter:
    
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(projection='3d')
    azim = 30
    elev = 20

    def __init__(self, top_len, stem_len, w, pd_dia=5, centers=None, rc=0, isShowStep=False):
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

        # self.t_shape = np.column_stack([x[mask], y[mask], np.zeros_like(x[mask])])
        self._t_mask = mask

    def _generate_ref_circ(self, diameter, n_ref_points):
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
        self.x_axes = np.array([[diameter / 2, 0, 0], [-diameter / 2, 0, 0]])
        self.y_axes = np.array([[0, diameter / 2, 0], [0, -diameter / 2, 0]])
        self.z_axes = np.array([[0, 0, diameter / 2], [0, 0, -diameter / 2]])

    def _generate_vals(self):
        self.vals = np.zeros([100, 100])

    def _rotate(self, coords):
        rotation = R.from_euler('ZYX', self.euler_angles, degrees=True)
        return rotation.apply(coords)
    
    def _displacement(self):
        displacement = np.zeros_like(self.vals)
        displacement[self._t_mask] = self.vals[self._t_mask]
        self.t_full[:, 2] = displacement.ravel()

    def _interpolate(self):
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
        self.ax.text('t = 0.0s')

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
                                            cmap=Colormap('crameri:roma').to_matplotlib(),
                                            vmax=1, vmin=-1,
                                            alpha=1)
            self.xy_line,  = self.ax.plot(self.xy_circle[:, 0], self.xy_circle[:, 1], self.xy_circle[:, 2],
                                        c='#31DBF5', label='XY Circle', alpha=1)
            self.yz_line,  = self.ax.plot(self.yz_circle[:, 0], self.yz_circle[:, 1], self.yz_circle[:, 2],
                                        c='#F56AAD', label='YZ Circle', alpha=1)
            self.zx_line,  = self.ax.plot(self.zx_circle[:, 0], self.zx_circle[:, 1], self.zx_circle[:, 2],
                                        c='#ADA666', label='ZX Circle', alpha=1)
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
        if self.isShowStep:
            print(frame)
        self.draw()

    def animate(self):
        self.init_canvas()
        self.anim = animation.FuncAnimation(self.fig, self.update_ani, interval=1,
                                            frames=len(self.pvs_data), repeat=False)
        plt.show()

# Read data
def main():
    pv_path = 'dataset/pv_raw/dry_cough.npy'
    or_path = 'dataset/orientation_raw/dry_cough_or_raw.txt'
    interval_path = 'dataset/orientation_raw/dry_cough_expanded_peaks.txt'

    pv = np.load(pv_path)[:, :4, :]
    ori = pd.read_csv(or_path, header=None, delimiter='\t').to_numpy()
    expanded_peaks = pd.read_csv(interval_path, header=None, delimiter='\t').to_numpy()
    pvs_array = np.mean(pv, axis=0).T
    angles_array = (np.mean(ori[:, 1:][expanded_peaks], axis=0) - np.mean(ori[:, 1:][expanded_peaks], axis=0)[0])*100

    plotter = TShapePlotter(4, 6, 2, pd_dia=10, rc=1)
    plotter.azim = 40
    plotter.elev = 30

    # Generate animation
    plotter.set_data(pvs_array, angles_array)
    plotter.init_canvas()
    plotter.animate()

    # ffwriter = animation.FFMpegWriter(fps=100)
    # plotter.anim.save('dry_cough.mp4', writer=ffwriter)

if __name__ == '__main__':
    main()