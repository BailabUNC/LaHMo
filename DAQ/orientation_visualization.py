import serial
import datetime
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def unpack_coords(coords):
    return coords[0], coords[1], coords[2]

def degree_to_rad(angle):
    return angle*np.pi/180

def write_line(f, str):
    f.write(str)
    f.write('\n')

def angles_to_coords(rho, yaw_degree, pitch_degree, roll_degree):
    # convert from degree to radian
    u = degree_to_rad(roll_degree)
    v = degree_to_rad(pitch_degree)
    w = degree_to_rad(yaw_degree)
    
    # generate rotation matrix from Euler angles
    r11 = np.cos(v)*np.cos(w)
    r12 = np.sin(u)*np.sin(v)*np.cos(w)-np.cos(u)*np.sin(w)
    r13 = np.sin(u)*np.sin(w)+np.cos(u)*np.sin(v)*np.cos(w)
    r21 = np.cos(v)*np.sin(w)
    r22 = np.cos(u)*np.cos(w)+np.sin(u)*np.sin(v)*np.sin(w)
    r23 = np.cos(u)*np.sin(v)*np.sin(w)-np.sin(u)*np.cos(w)
    r31 = -np.sin(v)
    r32 = np.sin(u)*np.cos(v)
    r33 = np.cos(u)*np.cos(v)
    R = np.array([[r11, r12, r13],
                  [r21, r22, r23],
                  [r31, r32, r33]])
    
    # calculate coordinates after rotation
    coordsl = np.array([rho, 0, 0]).T
    coordss = np.array([0, rho, 0]).T
    coordsn = np.array([0, 0, rho]).T
    
    return np.matmul(R, coordsl), np.matmul(R, coordss), np.matmul(R, coordsn)

def draw_vector_from_origin(ax, coords, color):
    # draw vector in ax
    x, y, z = unpack_coords(coords)
    line, = ax.plot([0, x], [0, y], [0, z], color=color)
    return line

def orientation_update(frame):
    try:
        with serial.Serial('COM30', 9600) as ser:
            ser_byte = ser.readline()
            decoded_byte = ser_byte.decode('utf-8')
            print(decoded_byte)
            yaw = float(decoded_byte.split('\t')[0])
            pitch = float(decoded_byte.split('\t')[1])
            roll = float(decoded_byte.split('\t')[2])
            coordsl, coordss, coordsn = angles_to_coords(rho, yaw, pitch, roll)
    except:
        return vecl, vecs, vecn
    xl, yl, zl = unpack_coords(coordsl)
    xs, ys, zs = unpack_coords(coordss)
    xn, yn, zn = unpack_coords(coordsn)
    vecl.set_data([0, xl], [0, yl])
    vecl.set_3d_properties([0, zl])
    vecs.set_data([0, xs], [0, ys])
    vecs.set_3d_properties([0, zs])
    vecn.set_data([0, xn], [0, yn])
    vecn.set_3d_properties([0, zn])
    return vecl, vecs, vecn

# Initialization
rho = 1
coordsl_init = [rho, 0, 0]
coordss_init = [0, rho, 0]
coordsn_init = [0, 0, rho]

# Generate image
fig = plt.figure(figsize=[10, 10])
ax = fig.add_subplot(projection='3d')
ax.set_xlim([-1.5*rho, 1.5*rho])
ax.set_ylim([-1.5*rho, 1.5*rho])
ax.set_zlim([-1.5*rho, 1.5*rho])
u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:20j]
x = np.cos(u)*np.sin(v)
y = np.sin(u)*np.sin(v)
z = np.cos(v)
ax.plot_surface(x, y, z, alpha=0.2)
ax.set_box_aspect((1, 1, 1))

vecl = draw_vector_from_origin(ax, coordsl_init, 'firebrick') # long axis init
vecs = draw_vector_from_origin(ax, coordss_init, 'limegreen') # short axis init
vecn = draw_vector_from_origin(ax, coordsn_init, 'midnightblue') # normal axis init

# Path to file specification
current_time = datetime.datetime.now()
filename = str(current_time.month)+str(current_time.day)+str(current_time.hour)+str(current_time.minute)+str(current_time.second)
path = 'dataset/orientation/0309/'+filename+'.txt'


# write to file
with open(path, 'a+') as f:
    start_s = time.time()
    write_line(f, '\t'.join(('Timestamp (ms)', 'Yaw (degree)', 'Pitch (degree)', 'Roll (degree)')))
    while True:
        try:
            with serial.Serial('COM30', 9600) as ser:
                ser_byte = ser.readline()
                decoded_byte = ser_byte.decode('utf-8')
                print(decoded_byte)
                
                now_s = time.time()
                timestamp = now_s - start_s
                yaw = float(decoded_byte.split('\t')[0])
                pitch = float(decoded_byte.split('\t')[1])
                roll = float(decoded_byte.split('\t')[2])
                write_line(f, '\t'.join((str(1000*timestamp), str(yaw), str(pitch), str(roll))))
        except IndexError:
            continue
        except ValueError:
            continue
        except KeyboardInterrupt:
            break

# Start animation
# anim = FuncAnimation(fig, orientation_update, interval=1)
# plt.show()