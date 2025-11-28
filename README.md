# YOLO Data Labeler

A comprehensive tkinter-based interface for labeling images for object detection training with both YOLO and PyTorch format support.

## Features

- **Image Loading & Navigation**: Load images from the `Unlabeled_Data` folder with next/previous navigation
- **Custom Label Management**: Create, edit, and remove custom labels for your objects
- **Interactive Annotation**: Click and drag to draw bounding boxes, right-click to delete
- **Multiple Output Formats**: Save annotations in YOLO, COCO, Pascal VOC, and custom PyTorch formats
- **Dataset Export**: Export complete train/validation datasets ready for PyTorch training
- **Auto-save/Load**: Automatically saves and loads existing annotations

## Quick Start

1. **Setup**: Install dependencies with `pip install -r requirements.txt`
2. **Add Images**: Place your images in the `Unlabeled_Data/` folder
3. **Run**: Execute `python DataLabeler.py`
4. **Label**: 
   - Load an image
   - Create labels
   - Draw bounding boxes by clicking and dragging
   - Save annotations
5. **Export**: Use "Export PyTorch Dataset" for complete train/val dataset

## Directory Structure

```
YOLO ObjectDetection/
├── DataLabeler.py          # Main application
├── requirements.txt        # Dependencies
├── Unlabeled_Data/        # Put your images here
│   └── *.jpg, *.png, etc.
└── Labeled_Data/          # All annotations saved here
    ├── *.txt              # YOLO format annotations
    ├── *.json             # Human-readable annotations
    ├── classes.txt        # Label definitions
    └── pytorch/           # PyTorch-compatible formats
        ├── annotations/   # COCO, VOC, and custom formats
        │   ├── *_coco.json
        │   ├── *.xml
        │   └── *_pytorch.json
        └── dataset/       # Complete exported datasets
            ├── images/
            │   ├── train/
            │   └── val/
            ├── annotations/
            │   ├── train/
            │   └── val/
            ├── dataset_info.json
            └── pytorch_dataset.py
```

## Output Formats

### 1. YOLO Format (`*.txt`)
Standard YOLO format with normalized coordinates:
```
class_id center_x center_y width height
```

### 2. COCO Format (`*_coco.json`)
Industry-standard format compatible with torchvision and Detectron2:
```json
{
  "images": [...],
  "annotations": [...],
  "categories": [...]
}
```

### 3. Pascal VOC Format (`*.xml`)
XML format widely supported by PyTorch libraries

### 4. Custom PyTorch Format (`*_pytorch.json`)
Clean, simple format for easy PyTorch integration

## Usage Instructions

### Basic Labeling
1. Click "Load Image" to select an image
2. Type a label name and click "Add Label"
3. Select the label from the list
4. Click and drag on the image to draw bounding boxes
5. Right-click on any box to delete it
6. Click "Save Annotations" when finished

### Format Selection
- **All Formats**: Saves YOLO + PyTorch formats
- **YOLO Only**: Traditional YOLO format only
- **PyTorch Only**: COCO, VOC, and custom PyTorch formats

### Dataset Export
1. Label multiple images
2. Click "Export PyTorch Dataset"
3. Choose train/validation split ratio (e.g., 0.8 = 80% train, 20% val)
4. Complete dataset with train/val splits will be created

## PyTorch Integration

The exported dataset includes a ready-to-use PyTorch Dataset class:

```python
from pytorch_dataset import get_data_loaders

# Load your labeled data
train_loader, val_loader = get_data_loaders("Labeled_Data/pytorch/dataset", batch_size=4)

# Use in training loop
for images, targets in train_loader:
    # images: batch of image tensors
    # targets: batch of dicts with 'boxes', 'labels', 'image_id'
    # Ready for your PyTorch model!
```

## Compatible Libraries

- **YOLO (v5, v8, etc.)**: Use YOLO format files
- **torchvision**: Use COCO format
- **Detectron2**: Use COCO format
- **MMDetection**: Use COCO format
- **Custom PyTorch models**: Use custom PyTorch format

## Tips

- **Minimum Box Size**: Boxes smaller than 5x5 pixels are automatically discarded
- **Navigation**: Use Next/Previous buttons to move between images efficiently
- **Persistent Labels**: Labels are saved and automatically loaded for each session
- **Annotation Persistence**: Existing annotations are automatically loaded when reopening images
- **Multiple Formats**: You can save in multiple formats simultaneously for maximum compatibility

## Requirements

- Python 3.6+
- tkinter (usually comes with Python)
- Pillow (PIL) for image processing

Install dependencies:
```bash
pip install -r requirements.txt
```
