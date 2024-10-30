import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib import colors
import tkinter as tk
from tkinter import simpledialog

# Global variables to control toggling of field lines and equipotential lines
show_field_lines = True
show_equipotential_lines = True
show_equipotential_map = False

# Function to compute electric field and potential due to a point charge, with masking
def compute_field(x, y, charges):
    Ex, Ey = np.zeros_like(x), np.zeros_like(y)
    V = np.zeros_like(x)
    mask = np.ones_like(x, dtype=bool)  # Mask to prevent plotting near charges
    
    for charge in charges:
        q, cx, cy = charge
        dx = x - cx
        dy = y - cy
        r = np.sqrt(dx**2 + dy**2) + 1e-20  # Avoid division by zero
        
        # Apply masking: Set to False (masked) near each charge
        mask &= r > 0.22  # Mask region within 0.3 units of the charge center
        
        Ex += q * dx / (r**3)
        Ey += q * dy / (r**3)
        V += q / r
        
    Ex = np.ma.masked_where(~mask, Ex)
    Ey = np.ma.masked_where(~mask, Ey)
    V = np.ma.masked_where(~mask, V)  # Mask the potential in the charge regions
    return Ex, Ey, V

# Function to handle mouse clicks and add/delete/modify charges
def onclick(event):
    global charges
    if event.inaxes:
        # Detect if user is clicking near an existing charge (to modify/delete)
        for i, charge in enumerate(charges):
            _, cx, cy = charge
            if np.hypot(event.xdata - cx, event.ydata - cy) < 0.3:
                if event.button == 3:  # Control click to delete
                    del charges[i]
                    plot_field()
                    return
                elif event.button == 1 and event.key == 'shift':  # Shift + Left click to modify
                    modify_charge_dialog(i)
                    return
        
        # Add new charge on left click (positive/negative based on left/right button)
        if event.button == 1:  # Left click for positive charge
            charge = 1
        elif event.button == 3:  # Right click for negative charge
            charge = -1

        else:
            return
        
        charges.append((charge, event.xdata, event.ydata))
        plot_field()

# Function to handle key presses for toggling field and equipotential lines
def onkeypress(event):
    global show_field_lines, show_equipotential_lines, show_equipotential_map
    if event.key == '1':
        show_field_lines = not show_field_lines
    elif event.key == '2':
        show_equipotential_lines = not show_equipotential_lines
    elif event.key == 'c':  # Check for 'C' key to clear charges
        clear_charges()
    elif event.key == '3':  # Check for 'm'
        show_equipotential_map = not show_equipotential_map
    elif event.key == 's':
            fields_save = input("Save as?")
            plt.savefig(field_save, format="jpg", dpi=1000)  # Adjust dpi for quality
    plot_field()

# Function to clear all charges
def clear_charges():
    global charges
    charges = []  # Clear the charges list
    plot_field()  # Replot the field to reflect changes

# Function to plot electric field and equipotential lines
def plot_field():
    global charges
    plt.clf()
    
    # Create a grid of points with higher resolution
    x = np.linspace(-10, 10, 1200)
    y = np.linspace(-10, 10, 1200)
    X, Y = np.meshgrid(x, y)
    
    # Compute the electric field and potential with masking
    Ex, Ey, V = compute_field(X, Y, charges)
    
    # Prepare starting points for field lines (around each charge)
    start_points = []
    for charge in charges:
        num_field_lines = int(abs(charge[0]) * 16)  # Number of field lines proportional to charge magnitude
        cx, cy = charge[1], charge[2]
        radius = 0.35  # Small distance away from the charge to start the field lines
        for i in range(num_field_lines):
            angle = 2 * np.pi * i / num_field_lines
            x_start = cx + radius * np.cos(angle)
            y_start = cy + radius * np.sin(angle)
            start_points.append([x_start, y_start])
    
    start_points = np.array(start_points)  # Convert list to numpy array with shape (n_points, 2)
    
    # Plot field lines using streamplot if toggled on
    if show_field_lines and len(start_points) > 0:
        plt.streamplot(X, Y, Ex, Ey, color='blue', linewidth=0.5, start_points=start_points, density=10.0)
    
    # Plot equipotential lines with a colormap if toggled on
    if show_equipotential_lines:
        equipotential_levels = np.linspace(-20, 20, 100)  # More levels for higher sensitivity
        plt.contour(X, Y, V, levels=equipotential_levels, colors='black', linewidths=0.5, alpha=0.7)

    if show_equipotential_map:
        # Define normalization range
        vmin = np.percentile(V.compressed(), 10)
        vmax = np.percentile(V.compressed(), 90)
        norm2 = colors.Normalize(vmin=vmin, vmax=vmax)
    
        # Use imshow to create a heatmap
        plt.imshow(V, extent=[x.min(), x.max(), y.min(), y.max()], origin='lower', 
               cmap='coolwarm', norm=norm2, alpha=0.7)

        # Add a colorbar to indicate potential values
        cbar = plt.colorbar(label='Potential (V)', extend='both')
        cbar.set_ticks([-3, 0, 3])
        cbar.set_ticklabels(["-", "0", "+"])
    
    # Plot the charges
    for charge in charges:
        q, cx, cy = charge
        color = 'r' if q > 0 else 'b'
        plt.gca().add_patch(Circle((cx, cy), 0.2, color=color))
    
    plt.xlim(-10, 10)
    plt.ylim(-10, 10)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.draw()

    
# Function to open a dialog for modifying an existing charge
def modify_charge_dialog(index):
    global charges
    
    # Create a simple Tkinter dialog to modify charge properties
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    q = charges[index][0]
    
    new_q = simpledialog.askfloat("Modify Charge", f"Current charge: {q}\nEnter new charge value:", initialvalue=q)
    
    if new_q is not None:
        charges[index] = (new_q, charges[index][1], charges[index][2])
    
    plot_field()

# Initialize charge list
charges = []

# Set up the plot
fig, ax = plt.subplots()
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.set_aspect('equal', adjustable='box')
ax.set_title('Left click: positive charge, Right click: negative charge\n1: toggle field lines, 2: toggle equipotential lines, C: clear charges')

# Connect the click and key press events to their respective functions
fig.canvas.mpl_connect('button_press_event', onclick)
fig.canvas.mpl_connect('key_press_event', onkeypress)

# Display the initial empty field
plot_field()

# Show the plot
plt.show()


