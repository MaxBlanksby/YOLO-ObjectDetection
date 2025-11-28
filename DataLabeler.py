import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime

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
        self.pytorch_path = os.path.join(self.labeled_path, "pytorch")
        
        # Create directories if they don't exist
        os.makedirs(self.unlabeled_path, exist_ok=True)
        os.makedirs(self.labeled_path, exist_ok=True)
        os.makedirs(self.pytorch_path, exist_ok=True)
        os.makedirs(os.path.join(self.pytorch_path, "annotations"), exist_ok=True)
        os.makedirs(os.path.join(self.pytorch_path, "images"), exist_ok=True)
        
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
        
        # Save format selection
        ttk.Label(save_frame, text="Save Format:").pack(anchor=tk.W)
        self.save_format = tk.StringVar(value="all")
        format_frame = ttk.Frame(save_frame)
        format_frame.pack(fill=tk.X, pady=2)
        
        ttk.Radiobutton(format_frame, text="All Formats", variable=self.save_format, value="all").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="YOLO Only", variable=self.save_format, value="yolo").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="PyTorch Only", variable=self.save_format, value="pytorch").pack(anchor=tk.W)
        
        ttk.Button(save_frame, text="Save Annotations", command=self.save_annotations).pack(fill=tk.X, pady=2)
        ttk.Button(save_frame, text="Export PyTorch Dataset", command=self.export_pytorch_dataset).pack(fill=tk.X, pady=2)
        
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
            save_format = self.save_format.get()
            
            img_width, img_height = self.current_image.size
            
            if save_format in ["all", "yolo"]:
                # Save in YOLO format
                txt_path = os.path.join(self.labeled_path, f"{filename}.txt")
                json_path = os.path.join(self.labeled_path, f"{filename}.json")
                
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
            
            if save_format in ["all", "pytorch"]:
                # Save PyTorch formats
                self.save_pytorch_formats(filename, img_width, img_height)
            
            self.status_var.set(f"Saved annotations: {filename}")
            
            # Show appropriate success message
            if save_format == "yolo":
                messagebox.showinfo("Success", f"YOLO annotations saved successfully!\n\nFiles created:\n- {filename}.txt (YOLO format)\n- {filename}.json (readable format)\n- classes.txt (label definitions)")
            elif save_format == "pytorch":
                messagebox.showinfo("Success", f"PyTorch annotations saved successfully!\n\nFiles created:\n- {filename}_coco.json (COCO format)\n- {filename}.xml (Pascal VOC format)\n- {filename}_pytorch.json (PyTorch format)")
            else:
                messagebox.showinfo("Success", f"All format annotations saved successfully!\n\nYOLO files: {filename}.txt, {filename}.json, classes.txt\nPyTorch files: {filename}_coco.json, {filename}.xml, {filename}_pytorch.json")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotations: {str(e)}")
    
    def save_pytorch_formats(self, filename, img_width, img_height):
        """Save annotations in PyTorch-compatible formats"""
        # 1. COCO format (commonly used with torchvision)
        coco_data = {
            "images": [{
                "id": 1,
                "width": img_width,
                "height": img_height,
                "file_name": f"{filename}.jpg"  # Assume jpg, adjust as needed
            }],
            "annotations": [],
            "categories": []
        }
        
        # Add categories
        for i, label in enumerate(self.labels):
            coco_data["categories"].append({
                "id": i + 1,  # COCO categories start from 1
                "name": label,
                "supercategory": "object"
            })
        
        # Add annotations
        for ann_id, annotation in enumerate(self.rectangles):
            x1, y1, x2, y2 = annotation['bbox']
            width = x2 - x1
            height = y2 - y1
            area = width * height
            
            label = annotation['label']
            category_id = self.labels.index(label) + 1 if label in self.labels else 1
            
            coco_data["annotations"].append({
                "id": ann_id + 1,
                "image_id": 1,
                "category_id": category_id,
                "bbox": [x1, y1, width, height],  # COCO format: [x, y, width, height]
                "area": area,
                "iscrowd": 0
            })
        
        # Save COCO format
        coco_path = os.path.join(self.pytorch_path, "annotations", f"{filename}_coco.json")
        with open(coco_path, 'w') as f:
            json.dump(coco_data, f, indent=2)
        
        # 2. Pascal VOC format (XML)
        self.save_pascal_voc_format(filename, img_width, img_height)
        
        # 3. PyTorch custom format
        pytorch_data = {
            "image_info": {
                "filename": f"{filename}.jpg",
                "width": img_width,
                "height": img_height,
                "channels": 3
            },
            "annotations": [],
            "classes": {label: i for i, label in enumerate(self.labels)}
        }
        
        for annotation in self.rectangles:
            x1, y1, x2, y2 = annotation['bbox']
            label = annotation['label']
            class_id = self.labels.index(label) if label in self.labels else 0
            
            pytorch_data["annotations"].append({
                "class_id": class_id,
                "class_name": label,
                "bbox": [x1, y1, x2, y2],  # [x1, y1, x2, y2] format
                "bbox_mode": "xyxy"
            })
        
        # Save PyTorch format
        pytorch_path = os.path.join(self.pytorch_path, "annotations", f"{filename}_pytorch.json")
        with open(pytorch_path, 'w') as f:
            json.dump(pytorch_data, f, indent=2)
    
    def save_pascal_voc_format(self, filename, img_width, img_height):
        """Save annotations in Pascal VOC XML format"""
        annotation = ET.Element("annotation")
        
        # Add folder
        folder = ET.SubElement(annotation, "folder")
        folder.text = "images"
        
        # Add filename
        filename_elem = ET.SubElement(annotation, "filename")
        filename_elem.text = f"{filename}.jpg"
        
        # Add path
        path = ET.SubElement(annotation, "path")
        path.text = self.current_image_path
        
        # Add source
        source = ET.SubElement(annotation, "source")
        database = ET.SubElement(source, "database")
        database.text = "Unknown"
        
        # Add size
        size = ET.SubElement(annotation, "size")
        width = ET.SubElement(size, "width")
        width.text = str(img_width)
        height = ET.SubElement(size, "height")
        height.text = str(img_height)
        depth = ET.SubElement(size, "depth")
        depth.text = "3"
        
        # Add segmented
        segmented = ET.SubElement(annotation, "segmented")
        segmented.text = "0"
        
        # Add objects
        for rect_annotation in self.rectangles:
            obj = ET.SubElement(annotation, "object")
            
            name = ET.SubElement(obj, "name")
            name.text = rect_annotation['label']
            
            pose = ET.SubElement(obj, "pose")
            pose.text = "Unspecified"
            
            truncated = ET.SubElement(obj, "truncated")
            truncated.text = "0"
            
            difficult = ET.SubElement(obj, "difficult")
            difficult.text = "0"
            
            bndbox = ET.SubElement(obj, "bndbox")
            x1, y1, x2, y2 = rect_annotation['bbox']
            
            xmin = ET.SubElement(bndbox, "xmin")
            xmin.text = str(int(x1))
            ymin = ET.SubElement(bndbox, "ymin")
            ymin.text = str(int(y1))
            xmax = ET.SubElement(bndbox, "xmax")
            xmax.text = str(int(x2))
            ymax = ET.SubElement(bndbox, "ymax")
            ymax.text = str(int(y2))
        
        # Save XML file
        tree = ET.ElementTree(annotation)
        xml_path = os.path.join(self.pytorch_path, "annotations", f"{filename}.xml")
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    
    def export_pytorch_dataset(self):
        """Export complete PyTorch dataset with train/val split"""
        try:
            # Get all labeled images
            labeled_files = []
            for file in os.listdir(self.labeled_path):
                if file.endswith('.json') and not file == 'classes.txt':
                    labeled_files.append(file.replace('.json', ''))
            
            if not labeled_files:
                messagebox.showwarning("Warning", "No labeled images found")
                return
            
            # Ask for train/val split ratio
            split_ratio = simpledialog.askfloat(
                "Train/Val Split", 
                "Enter train split ratio (0.0-1.0):\n(e.g., 0.8 for 80% train, 20% val)",
                initialvalue=0.8,
                minvalue=0.1,
                maxvalue=0.9
            )
            
            if split_ratio is None:
                return
            
            import random
            random.shuffle(labeled_files)
            split_idx = int(len(labeled_files) * split_ratio)
            train_files = labeled_files[:split_idx]
            val_files = labeled_files[split_idx:]
            
            # Create dataset structure
            dataset_path = os.path.join(self.pytorch_path, "dataset")
            os.makedirs(dataset_path, exist_ok=True)
            os.makedirs(os.path.join(dataset_path, "images", "train"), exist_ok=True)
            os.makedirs(os.path.join(dataset_path, "images", "val"), exist_ok=True)
            os.makedirs(os.path.join(dataset_path, "annotations", "train"), exist_ok=True)
            os.makedirs(os.path.join(dataset_path, "annotations", "val"), exist_ok=True)
            
            # Copy and organize files
            import shutil
            
            def copy_files(file_list, split_name):
                for filename in file_list:
                    # Copy image
                    image_path = os.path.join(self.unlabeled_path, f"{filename}.jpg")
                    if not os.path.exists(image_path):
                        # Try other extensions
                        for ext in ['.png', '.jpeg', '.bmp', '.tiff']:
                            test_path = os.path.join(self.unlabeled_path, f"{filename}{ext}")
                            if os.path.exists(test_path):
                                image_path = test_path
                                break
                    
                    if os.path.exists(image_path):
                        shutil.copy2(image_path, os.path.join(dataset_path, "images", split_name))
                    
                    # Copy annotations
                    for ann_file in [f"{filename}_coco.json", f"{filename}.xml", f"{filename}_pytorch.json"]:
                        src_path = os.path.join(self.pytorch_path, "annotations", ann_file)
                        if os.path.exists(src_path):
                            shutil.copy2(src_path, os.path.join(dataset_path, "annotations", split_name))
            
            copy_files(train_files, "train")
            copy_files(val_files, "val")
            
            # Create dataset info file
            dataset_info = {
                "dataset_name": "Custom Object Detection Dataset",
                "created": datetime.now().isoformat(),
                "num_classes": len(self.labels),
                "classes": {i: label for i, label in enumerate(self.labels)},
                "train_images": len(train_files),
                "val_images": len(val_files),
                "total_images": len(labeled_files),
                "train_split": split_ratio,
                "formats": ["coco", "pascal_voc", "pytorch_custom"]
            }
            
            with open(os.path.join(dataset_path, "dataset_info.json"), 'w') as f:
                json.dump(dataset_info, f, indent=2)
            
            # Create PyTorch dataset loader example
            self.create_pytorch_dataset_loader(dataset_path)
            
            messagebox.showinfo(
                "Success", 
                f"PyTorch dataset exported successfully!\n\n"
                f"Dataset location: {dataset_path}\n"
                f"Train images: {len(train_files)}\n"
                f"Val images: {len(val_files)}\n"
                f"Classes: {len(self.labels)}\n\n"
                f"Files created:\n"
                f"- dataset_info.json\n"
                f"- pytorch_dataset.py (example loader)\n"
                f"- images/train/ and images/val/\n"
                f"- annotations/train/ and annotations/val/"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PyTorch dataset: {str(e)}")
    
    def create_pytorch_dataset_loader(self, dataset_path):
        """Create example PyTorch dataset loader code"""
        loader_code = '''import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import json
import os
from torchvision import transforms

class CustomObjectDetectionDataset(Dataset):
    def __init__(self, root_dir, split='train', transform=None, target_transform=None):
        """
        Custom PyTorch Dataset for object detection
        
        Args:
            root_dir: Path to dataset directory
            split: 'train' or 'val'
            transform: Transform to apply to images
            target_transform: Transform to apply to targets
        """
        self.root_dir = root_dir
        self.split = split
        self.transform = transform
        self.target_transform = target_transform
        
        self.images_dir = os.path.join(root_dir, 'images', split)
        self.annotations_dir = os.path.join(root_dir, 'annotations', split)
        
        # Load dataset info
        with open(os.path.join(root_dir, 'dataset_info.json'), 'r') as f:
            self.dataset_info = json.load(f)
        
        # Get image files
        self.image_files = [f for f in os.listdir(self.images_dir) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        # Load image
        img_name = self.image_files[idx]
        img_path = os.path.join(self.images_dir, img_name)
        image = Image.open(img_path).convert('RGB')
        
        # Load annotations (PyTorch format)
        base_name = os.path.splitext(img_name)[0]
        ann_path = os.path.join(self.annotations_dir, f"{base_name}_pytorch.json")
        
        with open(ann_path, 'r') as f:
            annotations = json.load(f)
        
        # Extract bboxes and labels
        boxes = []
        labels = []
        
        for ann in annotations['annotations']:
            boxes.append(ann['bbox'])  # [x1, y1, x2, y2]
            labels.append(ann['class_id'])
        
        # Convert to tensors
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)
        
        target = {
            'boxes': boxes,
            'labels': labels,
            'image_id': torch.tensor([idx])
        }
        
        if self.transform:
            image = self.transform(image)
        
        if self.target_transform:
            target = self.target_transform(target)
        
        return image, target

# Example usage:
def get_data_loaders(dataset_path, batch_size=4):
    """Create train and validation data loaders"""
    
    # Define transforms
    train_transform = transforms.Compose([
        transforms.Resize((416, 416)),  # Resize for YOLO
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((416, 416)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    # Create datasets
    train_dataset = CustomObjectDetectionDataset(
        dataset_path, 
        split='train', 
        transform=train_transform
    )
    
    val_dataset = CustomObjectDetectionDataset(
        dataset_path, 
        split='val', 
        transform=val_transform
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True,
        collate_fn=lambda x: tuple(zip(*x))  # Custom collate for object detection
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False,
        collate_fn=lambda x: tuple(zip(*x))
    )
    
    return train_loader, val_loader

# Example training loop structure:
def train_model():
    """Example training loop structure"""
    dataset_path = "path/to/your/dataset"
    train_loader, val_loader = get_data_loaders(dataset_path)
    
    # Load your model here
    # model = YourModel(num_classes=len(dataset_info['classes']))
    
    for epoch in range(num_epochs):
        for batch_idx, (images, targets) in enumerate(train_loader):
            # Your training code here
            pass
            
        # Validation
        for batch_idx, (images, targets) in enumerate(val_loader):
            # Your validation code here
            pass

if __name__ == "__main__":
    # Test the dataset loader
    dataset_path = "."  # Current directory
    train_loader, val_loader = get_data_loaders(dataset_path, batch_size=2)
    
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    
    # Test loading one batch
    for images, targets in train_loader:
        print(f"Batch size: {len(images)}")
        print(f"Image shape: {images[0].shape}")
        print(f"Target keys: {targets[0].keys()}")
        break
'''
        
        loader_path = os.path.join(dataset_path, "pytorch_dataset.py")
        with open(loader_path, 'w') as f:
            f.write(loader_code)
    
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


