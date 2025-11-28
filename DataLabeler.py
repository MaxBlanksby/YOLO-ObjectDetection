import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import json

class DataLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Data Labeler")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.current_image = None
        self.current_image_path = None
        self.photo = None
        self.canvas_image = None
        self.labels = []
        self.current_label = ""
        self.rectangles = []
        self.current_rect = None
        self.start_x = None
        self.start_y = None
        self.image_scale = 1.0
        self.canvas_width = 800
        self.canvas_height = 600
        
        # Paths
        self.unlabeled_path = "Unlabeled_Data"
        self.labeled_path = "Labeled_Data"
        
        # Create directories if they don't exist
        os.makedirs(self.unlabeled_path, exist_ok=True)
        os.makedirs(self.labeled_path, exist_ok=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Left panel for controls
        control_frame = ttk.Frame(main_frame, padding="5")
        control_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # File operations
        file_frame = ttk.LabelFrame(control_frame, text="File Operations", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="Load Image", command=self.load_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Next Image", command=self.next_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Previous Image", command=self.prev_image).pack(fill=tk.X, pady=2)
        
        # Label management
        label_frame = ttk.LabelFrame(control_frame, text="Label Management", padding="5")
        label_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Current label entry
        ttk.Label(label_frame, text="Current Label:").pack(anchor=tk.W)
        self.label_entry = ttk.Entry(label_frame)
        self.label_entry.pack(fill=tk.X, pady=2)
        
        ttk.Button(label_frame, text="Add Label", command=self.add_label).pack(fill=tk.X, pady=2)
        
        # Labels listbox
        ttk.Label(label_frame, text="Available Labels:").pack(anchor=tk.W, pady=(10, 0))
        self.labels_listbox = tk.Listbox(label_frame, height=6)
        self.labels_listbox.pack(fill=tk.X, pady=2)
        self.labels_listbox.bind('<<ListboxSelect>>', self.on_label_select)
        
        ttk.Button(label_frame, text="Remove Selected Label", command=self.remove_label).pack(fill=tk.X, pady=2)
        
        # Rectangle operations
        rect_frame = ttk.LabelFrame(control_frame, text="Annotations", padding="5")
        rect_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(rect_frame, text="Instructions:").pack(anchor=tk.W)
        instructions = tk.Text(rect_frame, height=4, wrap=tk.WORD)
        instructions.insert(tk.END, "1. Select a label\n2. Click and drag on image to draw bounding box\n3. Right-click to delete annotation")
        instructions.config(state=tk.DISABLED)
        instructions.pack(fill=tk.X, pady=2)
        
        self.annotations_listbox = tk.Listbox(rect_frame, height=6)
        self.annotations_listbox.pack(fill=tk.X, pady=2)
        
        ttk.Button(rect_frame, text="Clear All Annotations", command=self.clear_annotations).pack(fill=tk.X, pady=2)
        
        # Save operations
        save_frame = ttk.LabelFrame(control_frame, text="Save", padding="5")
        save_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(save_frame, text="Save Annotations", command=self.save_annotations).pack(fill=tk.X, pady=2)
        
        # Image display
        canvas_frame = ttk.LabelFrame(main_frame, text="Image", padding="5")
        canvas_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=self.canvas_width, height=self.canvas_height)
        
        # Scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_rectangle)
        self.canvas.bind("<B1-Motion>", self.draw_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.end_rectangle)
        self.canvas.bind("<Button-3>", self.delete_annotation)  # Right click to delete
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Load an image to start labeling")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def load_image(self):
        """Load an image from the unlabeled data folder"""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select an image",
            initialdir=self.unlabeled_path,
            filetypes=filetypes
        )
        
        if file_path:
            self.load_image_file(file_path)
    
    def load_image_file(self, file_path):
        """Load a specific image file"""
        try:
            self.current_image_path = file_path
            self.current_image = Image.open(file_path)
            
            # Clear previous annotations
            self.clear_annotations()
            
            # Scale image to fit canvas while maintaining aspect ratio
            img_width, img_height = self.current_image.size
            scale_w = self.canvas_width / img_width
            scale_h = self.canvas_height / img_height
            self.image_scale = min(scale_w, scale_h, 1.0)  # Don't scale up
            
            new_width = int(img_width * self.image_scale)
            new_height = int(img_height * self.image_scale)
            
            # Resize image
            display_image = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(display_image)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Load existing annotations if they exist
            self.load_existing_annotations()
            
            filename = os.path.basename(file_path)
            self.status_var.set(f"Loaded: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def next_image(self):
        """Load the next image in the unlabeled folder"""
        if not self.current_image_path:
            messagebox.showwarning("Warning", "No image currently loaded")
            return
            
        try:
            files = self.get_image_files()
            if not files:
                messagebox.showinfo("Info", "No images found in unlabeled folder")
                return
                
            current_file = os.path.basename(self.current_image_path)
            if current_file in files:
                current_index = files.index(current_file)
                next_index = (current_index + 1) % len(files)
                next_file = files[next_index]
                self.load_image_file(os.path.join(self.unlabeled_path, next_file))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load next image: {str(e)}")
    
    def prev_image(self):
        """Load the previous image in the unlabeled folder"""
        if not self.current_image_path:
            messagebox.showwarning("Warning", "No image currently loaded")
            return
            
        try:
            files = self.get_image_files()
            if not files:
                messagebox.showinfo("Info", "No images found in unlabeled folder")
                return
                
            current_file = os.path.basename(self.current_image_path)
            if current_file in files:
                current_index = files.index(current_file)
                prev_index = (current_index - 1) % len(files)
                prev_file = files[prev_index]
                self.load_image_file(os.path.join(self.unlabeled_path, prev_file))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load previous image: {str(e)}")
    
    def get_image_files(self):
        """Get list of image files in unlabeled folder"""
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        files = []
        for file in os.listdir(self.unlabeled_path):
            if os.path.splitext(file.lower())[1] in extensions:
                files.append(file)
        return sorted(files)
    
    def add_label(self):
        """Add a new label to the list"""
        label = self.label_entry.get().strip()
        if label and label not in self.labels:
            self.labels.append(label)
            self.labels_listbox.insert(tk.END, label)
            self.label_entry.delete(0, tk.END)
            self.status_var.set(f"Added label: {label}")
    
    def remove_label(self):
        """Remove selected label from the list"""
        selection = self.labels_listbox.curselection()
        if selection:
            index = selection[0]
            removed_label = self.labels[index]
            del self.labels[index]
            self.labels_listbox.delete(index)
            self.status_var.set(f"Removed label: {removed_label}")
    
    def on_label_select(self, event):
        """Handle label selection"""
        selection = self.labels_listbox.curselection()
        if selection:
            self.current_label = self.labels[selection[0]]
            self.status_var.set(f"Selected label: {self.current_label}")
    
    def start_rectangle(self, event):
        """Start drawing a rectangle"""
        if not self.current_image or not self.current_label:
            if not self.current_image:
                messagebox.showwarning("Warning", "Please load an image first")
            else:
                messagebox.showwarning("Warning", "Please select a label first")
            return
            
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        # Create initial rectangle
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2, tags="annotation"
        )
    
    def draw_rectangle(self, event):
        """Update rectangle while dragging"""
        if self.current_rect:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, cur_x, cur_y)
    
    def end_rectangle(self, event):
        """Finish drawing rectangle and save annotation"""
        if self.current_rect:
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            
            # Ensure minimum size
            if abs(end_x - self.start_x) < 5 or abs(end_y - self.start_y) < 5:
                self.canvas.delete(self.current_rect)
                self.current_rect = None
                return
            
            # Convert canvas coordinates to image coordinates
            img_x1 = self.start_x / self.image_scale
            img_y1 = self.start_y / self.image_scale
            img_x2 = end_x / self.image_scale
            img_y2 = end_y / self.image_scale
            
            # Ensure coordinates are in correct order
            x1, x2 = sorted([img_x1, img_x2])
            y1, y2 = sorted([img_y1, img_y2])
            
            # Store annotation
            annotation = {
                'label': self.current_label,
                'bbox': [x1, y1, x2, y2],
                'canvas_id': self.current_rect
            }
            self.rectangles.append(annotation)
            
            # Update annotations listbox
            self.update_annotations_list()
            
            self.current_rect = None
            self.status_var.set(f"Added annotation: {self.current_label}")
    
    def delete_annotation(self, event):
        """Delete annotation at click position"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Find overlapping items
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        for item in items:
            if "annotation" in self.canvas.gettags(item):
                # Find and remove the annotation
                for i, annotation in enumerate(self.rectangles):
                    if annotation['canvas_id'] == item:
                        self.canvas.delete(item)
                        del self.rectangles[i]
                        self.update_annotations_list()
                        self.status_var.set("Deleted annotation")
                        return
    
    def clear_annotations(self):
        """Clear all annotations"""
        self.canvas.delete("annotation")
        self.rectangles = []
        self.update_annotations_list()
        self.status_var.set("Cleared all annotations")
    
    def update_annotations_list(self):
        """Update the annotations listbox"""
        self.annotations_listbox.delete(0, tk.END)
        for i, annotation in enumerate(self.rectangles):
            bbox = annotation['bbox']
            text = f"{i+1}. {annotation['label']} ({bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f})"
            self.annotations_listbox.insert(tk.END, text)
    
    def save_annotations(self):
        """Save annotations to file"""
        if not self.current_image_path or not self.rectangles:
            messagebox.showwarning("Warning", "No image loaded or no annotations to save")
            return
            
        try:
            # Get image filename without extension
            filename = os.path.splitext(os.path.basename(self.current_image_path))[0]
            
            # Save in YOLO format
            txt_path = os.path.join(self.labeled_path, f"{filename}.txt")
            json_path = os.path.join(self.labeled_path, f"{filename}.json")
            
            img_width, img_height = self.current_image.size
            
            # Save YOLO format (class_id center_x center_y width height - normalized)
            with open(txt_path, 'w') as f:
                for annotation in self.rectangles:
                    label = annotation['label']
                    if label in self.labels:
                        class_id = self.labels.index(label)
                    else:
                        class_id = 0
                    
                    x1, y1, x2, y2 = annotation['bbox']
                    
                    # Convert to YOLO format (normalized center coordinates and dimensions)
                    center_x = (x1 + x2) / 2 / img_width
                    center_y = (y1 + y2) / 2 / img_height
                    width = (x2 - x1) / img_width
                    height = (y2 - y1) / img_height
                    
                    f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
            
            # Save JSON format for easier reading
            annotations_data = {
                'image_path': self.current_image_path,
                'image_size': [img_width, img_height],
                'labels': self.labels,
                'annotations': []
            }
            
            for annotation in self.rectangles:
                annotations_data['annotations'].append({
                    'label': annotation['label'],
                    'bbox': annotation['bbox']
                })
            
            with open(json_path, 'w') as f:
                json.dump(annotations_data, f, indent=2)
            
            # Also save labels list
            labels_path = os.path.join(self.labeled_path, "classes.txt")
            with open(labels_path, 'w') as f:
                for label in self.labels:
                    f.write(f"{label}\n")
            
            self.status_var.set(f"Saved annotations: {filename}")
            messagebox.showinfo("Success", f"Annotations saved successfully!\n\nFiles created:\n- {filename}.txt (YOLO format)\n- {filename}.json (readable format)\n- classes.txt (label definitions)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotations: {str(e)}")
    
    def load_existing_annotations(self):
        """Load existing annotations if they exist"""
        if not self.current_image_path:
            return
            
        filename = os.path.splitext(os.path.basename(self.current_image_path))[0]
        json_path = os.path.join(self.labeled_path, f"{filename}.json")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                # Load labels if they exist
                if 'labels' in data and data['labels']:
                    for label in data['labels']:
                        if label not in self.labels:
                            self.labels.append(label)
                            self.labels_listbox.insert(tk.END, label)
                
                # Load annotations
                for annotation in data['annotations']:
                    x1, y1, x2, y2 = annotation['bbox']
                    
                    # Convert to canvas coordinates
                    canvas_x1 = x1 * self.image_scale
                    canvas_y1 = y1 * self.image_scale
                    canvas_x2 = x2 * self.image_scale
                    canvas_y2 = y2 * self.image_scale
                    
                    # Create rectangle on canvas
                    rect_id = self.canvas.create_rectangle(
                        canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                        outline="red", width=2, tags="annotation"
                    )
                    
                    # Store annotation
                    self.rectangles.append({
                        'label': annotation['label'],
                        'bbox': [x1, y1, x2, y2],
                        'canvas_id': rect_id
                    })
                
                self.update_annotations_list()
                self.status_var.set(f"Loaded existing annotations for {filename}")
                
            except Exception as e:
                print(f"Error loading existing annotations: {e}")

def main():
    root = tk.Tk()
    app = DataLabeler(root)
    root.mainloop()

if __name__ == "__main__":
    main()


